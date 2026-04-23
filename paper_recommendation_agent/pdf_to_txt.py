import fitz
import json
import os
import re

# 配置常量
JSON_PATH = "papers.json"
PDF_DIR = "paper_pdf"
TXT_DIR = "paper_txt"

def setup_txt_folder():
    if not os.path.exists(TXT_DIR):
        os.makedirs(TXT_DIR)

def clean_academic_text(text):
    """
    针对学术论文排版的深度清理逻辑
    """
    if not text:
        return ""
    
    # 1. 修复被换行符切断的单词 (例如: struc- \n tured -> structured)
    # 匹配：字母 + 连字符 + 换行符 + 字母
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # 2. 修复同一段落内的硬换行
    # 原理：如果一行末尾不是句号/问号等结束符，且下一行开头是小写字母，通常是同一句
    text = re.sub(r'(?<![\.\!\?])\n\s*([a-z])', r' \1', text)
    
    # 3. 清理多余的空格和重复空行
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def extract_text_advanced(pdf_path):
    """
    使用块分析模式提取文本，并进行排版修复
    """
    full_text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                # 使用 sort=True 自动处理双栏阅读顺序
                page_text = page.get_text("text", sort=True)
                full_text += page_text + "\n"
        
        # 执行深度清理
        cleaned_text = clean_academic_text(full_text)
        return cleaned_text
    except Exception as e:
        print(f"  [错误] 无法解析 {pdf_path}: {e}")
        return None

def main():
    setup_txt_folder()

    if not os.path.exists(JSON_PATH):
        print(f"错误: 未找到 {JSON_PATH}")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        papers = json.load(f)

    total = len(papers)
    success_count = 0

    print(f"开始执行『深度修复模式』转换 {total} 篇 PDF...")

    for i, paper in enumerate(papers):
        arxiv_id = paper['arxiv_id']
        pdf_path = paper.get('pdf_path', "")
        
        if not pdf_path or not os.path.exists(pdf_path):
            pdf_path = os.path.join(PDF_DIR, f"{arxiv_id}.pdf")
            if not os.path.exists(pdf_path):
                continue

        txt_path = os.path.join(TXT_DIR, f"{arxiv_id}.txt")

        # 执行高级提取
        content = extract_text_advanced(pdf_path)
        
        if content:
            with open(txt_path, 'w', encoding='utf-8') as f_txt:
                f_txt.write(content)
            
            paper['txt_path'] = txt_path
            success_count += 1
            if (i+1) % 10 == 0:
                print(f"  进度: [{i+1}/{total}] 已完成...")

    with open(JSON_PATH, 'w', encoding='utf-8') as f_json:
        json.dump(papers, f_json, ensure_ascii=False, indent=4)

    print(f"\n✅ 转换完成！修复了双栏换行问题。成功: {success_count}/{total}")

if __name__ == "__main__":
    main()