from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import PyPDF2
import io
import requests
import os
from dotenv import load_dotenv
import logging
from openai import OpenAI  # Import the OpenAI client
import json
from openai import APIError, AuthenticationError, BadRequestError, RateLimitError, APIConnectionError

# 初始化Flask应用
app = Flask(__name__)
CORS(app)
load_dotenv()  # 加载环境变量

# 配置
app.config.update({
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB文件大小限制
    'UPLOAD_FOLDER': './uploads',
    'ALLOWED_EXTENSIONS': {'pdf'}
})

# 日志配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



API_CONFIG_MAX_TOKENS = 8192

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
if not deepseek_api_key:
    logger.error("DEEPSEEK_API_KEY not found in .env file or environment variables. Please set it.")

client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")




#检查是否上传的是pdf,且归一化PDF&pdf。返回0/1
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
def extract_text_from_pdf(file_stream):
    """从PDF文件流中提取文本内容"""
    try:
        reader = PyPDF2.PdfReader(file_stream)
        text = "\n".join([page.extract_text() for page in reader.pages])
        return text[:5000]  # 限制提取前5000个字符
    except Exception as e:
        logger.error(f"PDF解析失败: {str(e)}")
        return None




# 以下为“【3】 提取PDF文本+构造prompt"
def build_final_prompt(question, options, pdf_content=None):
    """构建最终发送给大模型的prompt"""
    prompt_map = {

        "first-contact": "我将要预习这部分本科生课程知识内容，希望获得一个非常棒的preview。可以辅以使用生活化类比和简单示例",
        "some-knowledge": "我处于初学阶段尾声，我希望从知识演进的角度把学到的这些分立的知识点连起来。就是说，我希望”把故事讲完整、听完整“。突出起到桥梁/粘合剂作用的内，容系统化梳理知识体系",
        "confused": "我希望你的回答内容主要围绕对比剖析和正反示例澄清展开，给我讲清楚讲透彻",
        "exam-focused": "突出考试重点和常见考查形式",

        "conceptual": "聚焦对这部分关键知识概念的本质分析",
        "structural": "注意体现知识之间相互的结构",
        "application": "包含对初学者友好的前沿实际问题场景拓展",
        "historical": "讲讲这门学科/这部分知识历史发展脉络",

        "mindmap": "注意提供有助于我形成bigger picture的回答内容，就好像是以一种学通透了的境界居高临下地看整个知识体系",#用Markdown格式输出可转换为思维导图的结构
        "key-points": "尽可能用含有相应主题emoji的文字，列出核心要点，增加趣味性",
        "flowchart": "知识如何承前启后呢？用到了哪些已学过的课程？将要新学哪些核心内容？给出学习路径的流程图建议，用→表示步骤关系",
        "qna": "我希望你回答的全文内容主要是给出3-5个关键自测问题并附简要答案",

        "deductive": "采用从一般原理到具体应用的演绎推理方式",
        "inductive": "通过具体案例归纳总结一般规律",
        "analogical": "建立与该课程其他部分知识可能的知识类比连接",
        "critical": "包含对现有理论的批判性思考",

        "textbook": "推荐广受好评的经典英文、中文教材各一本。并分别用一句话概述它们的特色",
        "video" : "优先推荐B站、YouTube，该课程/章节/内容广受好评的名师/名校优质课程。计算机科学相关的内容优先推荐MIT/UC Berkley/卡内基梅隆或斯坦福大学的lectures，给出可供点击直接跳转的链接",
        "practice": "针对该知识点设一道初级练习题，并附上关键解题思路",
        "case": "提供典型案例和分析框架"

    }

    prompt = f"""我是一名计算机专业本科生，我即将初次学习

**学生问题**: {question}

**学习阶段**: {prompt_map[options[0]]}
**学习维度**: {prompt_map[options[1]]}
**输出形式**: {prompt_map[options[2]]}
**思维模式**: {prompt_map[options[3]]}
**学习资源**: {prompt_map[options[4]]}"""
    if pdf_content:
        prompt += f"\n\n**课程资料摘要**:\n{pdf_content[:2000]}..."

    prompt += """

请用内容尽可能详细（字数尽可能多）并且结构清晰的中文回答，包含：
1. 核心概念定义
2. 知识结构展示
3. 学习路径展望
4. 知识承前启后
5. 优质资源推荐"""

    return prompt



 # ！正式开始通过Flask接入Web
@app.route('/process', methods=['POST'])
def process_request():
    try:
        question = request.form.get('question')
        options_str = request.form.get('options')
        file = request.files.get('file')

        if not question and not file:
            logger.warning("Empty request: No question or file provided.")
            return jsonify({"error": "请输入问题或上传文件"}), 400

        options = []
        if options_str:
            try:
                options = json.loads(options_str)
            except json.JSONDecodeError:
                logger.error(f"JSON解析错误: {options_str}")
                return jsonify({"error": "请求参数错误: 选项格式不正确。"}), 400

        pdf_content = ""
        if file and allowed_file(file.filename):
            try:
                pdf_content = extract_text_from_pdf(file)
                logger.info(f"PDF '{file.filename}' processed. Content length: {len(pdf_content)}.")
            except Exception as e:
                logger.error(f"PDF解析错误: {file.filename} - {e}", exc_info=True)
                pdf_content = "[PDF内容提取失败]"
        elif file:
            logger.warning(f"Illegal file type uploaded: {file.filename}")
            return jsonify({"error": "上传文件失败: 仅支持PDF文件。"}), 400

        # 即使PDF内容提取失败，也要尝试构建Prompt，因为可能只有文本问题
        final_prompt = build_final_prompt(question, options, pdf_content)
        logger.info(f"Generated prompt: {final_prompt[:200]}...")  # 打印前200字符

        #  Calling DeepSeek API using OpenAI SDK ---
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是就读于清华大学计算机系的大四本科生，对于中国大学计算机本科阶段的课程你学的非常好，不但具体知识点你都精通，而且你对于计算机系涉及到的每一门课程（包含数学基础课如线性代数和微积分）,你都有一个“bigger picture”。"
                                                  "你十分清楚计算机系本科的任何一门课当中，哪些是主干知识，哪些只是”旁支”。用Richard Feynman教授的话说，你做到了“Understand.Don't memorize.Learn principles,not formulas.”."
                                                  "并且能把你的深刻理解用易于初学者理解的语言表述出来，帮助一门课的初学者站在一定程度上的“全局高度”Get到一门课某一章、某一节的Bigger picture，使他们不至于在预习阶段和听讲时陷入课本里的细枝末节里，或是关注点跑偏。"
                                                  "并且你的回答字数总是宁多不少，十分详细"},
                    {"role": "user", "content": final_prompt},
                ],
                temperature=1.0,
                max_tokens=API_CONFIG_MAX_TOKENS,
                stream=False
            )

            # Extract the content from the SDK response object
            answer = response.choices[0].message.content
            logger.info("DeepSeek API call successful.")
            return jsonify({"answer": answer})

        except Exception as api_e:
            logger.error(f"DeepSeek API调用失败: {api_e}", exc_info=True)
            # Check for specific error types if possible, e.g., api_e.response.status_code
            return jsonify({"error": "大模型服务暂不可用，请稍后再试。"}), 500

    except Exception as e:
        logger.error(f"处理请求时发生未知错误: {e}", exc_info=True)
        return jsonify({"error": "服务器内部错误，请联系管理员。"}), 500


@app.route('/')
def index():
    return "Backend is running. Please open the HTML file directly in your browser."


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
