import json

def verify_papers(file_path="papers.json"):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 1. 检查总数
        total_count = len(data)
        
        # 2. 检查唯一性 (基于 arxiv_id) [cite: 66, 67]
        all_ids = [paper.get('arxiv_id') for paper in data]
        unique_ids = set(all_ids)
        unique_count = len(unique_ids)
        
        # 3. 检查字段完整性 (以第一条为例) [cite: 66-79]
        required_fields = ["arxiv_id", "title", "authors", "abstract", "published", "categories", "arxiv_url"]
        missing_fields = []
        if data:
            for field in required_fields:
                if field not in data[0]:
                    missing_fields.append(field)

        print("-" * 30)
        print(f"📊 数据统计报告:")
        print(f">> 总记录数: {total_count}")
        print(f">> 唯一论文数: {unique_count}")
        print(f">> 重复条目数: {total_count - unique_count}")
        
        if missing_fields:
            print(f"⚠️  警告: 缺少必要字段: {missing_fields}")
        else:
            print(f"✅ 字段检查: 完整 (包含 arxiv_id, abstract 等)") 
        if total_count == 200 and unique_count == 200:
            print("\n🌟 恭喜！数据完美达标，可以进行下一步下载 PDF。")
        else:
            print("\n❌ 数据尚不达标，请检查爬取逻辑。")
        print("-" * 30)

    except FileNotFoundError:
        print("❌ 错误：未找到 papers.json 文件。")
    except Exception as e:
        print(f"❌ 发生异常: {e}")

if __name__ == "__main__":
    verify_papers()