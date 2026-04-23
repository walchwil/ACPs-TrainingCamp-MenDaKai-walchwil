import json
import os
import time
import random
import urllib.request

# 配置常量
JSON_PATH = "papers.json"
PDF_DIR = "paper_pdf" # [cite: 5, 17, 59]

def setup_pdf_folder():
    """初始化文件夹 [cite: 17, 59]"""
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)

def download_direct(arxiv_id, target_path):
    """跳过官方库 API，直接从文件服务器搬运 PDF"""
    # 构造直接下载链接
    download_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36',
    }
    
    try:
        req = urllib.request.Request(download_url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(target_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"  [重创] {arxiv_id} 下载依然失败: {e}")
        return False

def main():
    setup_pdf_folder()
    
    if not os.path.exists(JSON_PATH):
        print("错误：未找到 papers.json")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        papers = json.load(f)

    print(f"开始执行『直接下载』模式，跳过 API 查询...")

    for i, paper in enumerate(papers):
        arxiv_id = paper['arxiv_id']
        file_name = f"{arxiv_id}.pdf" # [cite: 18, 61]
        file_path = os.path.join(PDF_DIR, file_name)

        # 核心：断点续传（跳过已成功下载的 145 篇）
        if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
            paper['pdf_path'] = file_path # [cite: 12, 58]
            continue

        print(f"[{i+1}/{len(papers)}] 正在补漏: {arxiv_id}...")
        
        if download_direct(arxiv_id, file_path):
            paper['pdf_path'] = file_path # [cite: 58]
            # 每下载一篇，随机休息，防止被封 IP
            time.sleep(random.uniform(8, 15))
        else:
            # 如果连续失败，建议手动断开热点重连
            print("  检测到网络阻断，建议切换热点 IP 后重试。")
            time.sleep(20)

        # 每 5 篇存一次盘
        if (i + 1) % 5 == 0:
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(papers, f, ensure_ascii=False, indent=4)

    # 最终保存 [cite: 16, 53]
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=4)

    print("\n✅ 补漏完成！请检查 paper_pdf 文件夹。")

if __name__ == "__main__":
    main()