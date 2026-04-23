import crawler
import download_pdf
import pdf_to_txt
import os

def run_pipeline():
    print("="*30)
    print("🚀 开始执行：arXiv 论文采集自动化流水线")
    print("="*30)

    # 1. 运行爬虫模块 [cite: 6, 31]
    print("\n[步骤 1/3] 正在抓取论文元数据...")
    crawler.fetch_papers() 

    # 2. 运行下载模块 [cite: 7, 42]
    print("\n[步骤 2/3] 正在下载 PDF 文件 (带断点续传)...")
    download_pdf.download_all_pdfs()

    # 3. 运行转换模块 [cite: 14, 43]
    print("\n[步骤 3/3] 正在提取纯文本内容...")
    pdf_to_txt.main()

    print("\n" + "="*30)
    print("✅ 所有任务已完成！")
    print(f"元数据记录：papers.json") 
    print(f"PDF 文件夹：paper_pdf/") 
    print(f"文本文件夹：paper_txt/") 
    print("="*30)

if __name__ == "__main__":
    run_pipeline()