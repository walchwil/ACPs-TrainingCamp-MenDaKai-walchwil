import arxiv
import json
import os
import time

# 配置常量
JSON_PATH = "papers.json"
PDF_DIR = "paper_pdf" # 对应作业要求文件夹 [cite: 17, 59]

def download_all_pdfs():
    # 1. 环境准备
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)
        print(f"已创建文件夹: {PDF_DIR}")

    if not os.path.exists(JSON_PATH):
        print(f"错误：找不到 {JSON_PATH}，请先运行 crawler.py")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        papers = json.load(f)

    # 2. 初始化官方客户端 (保持和爬取时一样的低频节奏)
    client = arxiv.Client(
        page_size=1, 
        delay_seconds=10.0, # 下载 PDF 消耗更大，建议维持 10s 间隔
        num_retries=5
    )

    print(f"开始使用官方库下载 {len(papers)} 篇论文...")

    for i, paper in enumerate(papers):
        arxiv_id = paper['arxiv_id']
        # 严格按要求命名: (arxiv_id).pdf [cite: 18, 61]
        file_name = f"{arxiv_id}.pdf"
        file_path = os.path.join(PDF_DIR, file_name)

        # 断点续传逻辑
        if os.path.exists(file_path):
            print(f"[{i+1}/{len(papers)}] {file_name} 已存在，跳过。")
            paper['pdf_path'] = file_path
            continue

        try:
            print(f"[{i+1}/{len(papers)}] 正在下载 {arxiv_id}...")
            # 使用官方库的 id_list 查询功能定位特定论文
            search = arxiv.Search(id_list=[arxiv_id])
            paper_obj = next(client.results(search))
            
            # 直接调用官方下载方法
            paper_obj.download_pdf(dirpath=PDF_DIR, filename=file_name)
            
            # 更新 JSON 路径字段 [cite: 12, 58]
            paper['pdf_path'] = file_path
            
            # 实时保存，防止断电
            if (i + 1) % 5 == 0:
                with open(JSON_PATH, 'w', encoding='utf-8') as f:
                    json.dump(papers, f, ensure_ascii=False, indent=4)
                    
        except StopIteration:
            print(f"  [警告] 未能从 API 找到 ID 为 {arxiv_id} 的论文信息")
        except Exception as e:
            print(f"  [错误] 下载 {arxiv_id} 时发生异常: {e}")
            # 如果连续出错，建议停下来换个热点
            time.sleep(30)

    # 3. 最终写入更新后的 JSON
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=4)
    
    print("\n[下载完成] 所有 PDF 已就位，JSON 路径已更新。")

if __name__ == "__main__":
    download_all_pdfs()