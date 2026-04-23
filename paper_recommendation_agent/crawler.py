import arxiv
import json
import os
import re
import time

OUTPUT_JSON = "papers.json"
CATEGORIES_QUOTA = {"cs.CL": 60, "cs.AI": 70, "cs.IR": 70}

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def fetch_papers():
    all_papers = []
    seen_ids = set() # 核心：去重记录器
    
    client = arxiv.Client(page_size=100, delay_seconds=10.0, num_retries=10)
    
    for category, quota in CATEGORIES_QUOTA.items():
        print(f"\n>>> 攻克分类: {category} (目标 unique {quota} 篇)")
        
        # 为了应对去重导致的损耗，我们请求比 quota 稍多一点的数据
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=quota + 20, # 多取20篇备用
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        cat_count = 0
        try:
            for result in client.results(search):
                aid = result.get_short_id()
                
                # 跨分类去重判断
                if aid in seen_ids:
                    continue
                
                if cat_count >= quota:
                    break
                
                paper = {
                    "arxiv_id": aid,
                    "title": clean_text(result.title),
                    "authors": [a.name for a in result.authors],
                    "abstract": clean_text(result.summary),
                    "published": result.published.strftime("%Y-%m-%d"),
                    "categories": result.categories,
                    "arxiv_url": result.entry_id,
                    "pdf_path": "", 
                    "txt_path": ""
                }
                all_papers.append(paper)
                seen_ids.add(aid)
                cat_count += 1
            
            print(f"  [完成] {category} 贡献了 {cat_count} 篇唯一论文。")
                
        except Exception as e:
            print(f"  [出错] {e}")

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=4)
    
    print(f"\n[最终结果] 唯一论文总数: {len(all_papers)}")

if __name__ == "__main__":
    fetch_papers()