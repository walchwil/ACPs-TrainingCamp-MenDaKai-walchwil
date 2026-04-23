

# 实验报告：基于 arXiv官方库的论文爬取与数据清洗

### 门大开    2023212070   2023219105班



------

## 1. 选题说明

本次实验从 arXiv 爬取计算机科学领域的论文，具体分类及配额如下：

- **cs.CL (Computation and Language)**：60 篇。 
- **cs.AI (Artificial Intelligence)**：70 篇。 
- **cs.IR (Information Retrieval)**：70 篇。 
- **总计**：200 篇唯一论文。

**选题原因**：
	1.我对自然语言处理（CL）与信息检索（IR）的交叉领域比较感兴趣 ，且当前的趋势是利用大模型优化知识图谱问答KGQA、检索增强生成RAG。
	2.这三个方向个论文中，LaTex公式相对较少，(cs.LG方向论文数学性较强，经常包含收敛性证明、复杂度分析等数学推导）；论文中的图片也不如CV领域多（cs.CV方向的论文通常包含大量的消融实验对比图、热力图、生成图）。
	3.前期数据清洗工作可以做出很好的效果。选择这三个分类可以为后续作业提供高质量的科研数据基础。



------

## 2. 爬虫介绍

分文件编写，将数据流拆分为三个独立脚本，通过 `main.py` 实现一键串联运行：

1. **`crawler.py`**：调用 arXiv API 抓取元数据，支持按日期过滤，生成 `papers.json` 。
2. **`download_pdf_arXiv.py`**：用官方API解析 JSON 任务列表，将论文 PDF 批量下载至 `paper_pdf/` 
   **`download_pdf_urllib.py`**：应对官方API的  **429报错** ，通过**更底层的方式**将论文 PDF 批量下载至 `paper_pdf/` 。
3. **`pdf_to_txt.py`**：利用 `PyMuPDF`库 解析 PDF 物理块，清洗并提取纯文本至 `paper_txt/` 。

### 代码库总览

![image-20260327120650034](C:\Users\门大开\AppData\Roaming\Typora\typora-user-images\image-20260327120650034.png)

脚本说明：
crawler.py：爬虫，用arxiv官方库
check_data.py：用来检验是否是200篇不同的文章（防止同篇文章同时属于CL、AI、IR），
download_pdf_arXiv：是用官方库下载pdf（成功下载了188篇，剩下12篇怎么都是429报错）
download_pdf_urllib：是用urllib方案绕过官方库直接下载pdf(后来成功解决了429报错问题)
pdf_to_txt.py：用PyMuPDF库完成转换，解决了排版问题
main.py：主脚本

------

## 3. 实验过程中的问题与解决方法

本次实验远非一帆风顺。经历了多次从**请求被封**到**完美解析**曲折：

### (1) HTTP 429 频率封锁、转战**Colab**、仍失败，回到vscode换思路重写脚本

**问题**：最初使用 Python 原生 `urllib` 编写 `crawler.py`。即便引入了指数退避（Exponential Backoff），仍然频繁触发 **HTTP 429 (Too Many Requests)** 错误。切换手机热点、尝试 Colab 环境均因 IP 被 arXiv 标记而失败。

**解决方法**：

放弃原生请求，换用 **`arxiv` 官方 Python 库**。官方库内置了更符合 arXiv 规范的 Header 指纹和请求频率控制。配合 10 秒的延时，最后在手机热点环境下稳定拿到了 200 条元数据。


![39a401c7279b9702e630b78576861077](C:\Users\门大开\xwechat_files\wxid_0vfnva4kjvx432_4317\temp\RWTemp\2026-03\39a401c7279b9702e630b78576861077.png)
### (2) 网络波动与断点续传机制

**问题**：在下载 PDF 阶段，中间我换了教室。楼梯间网络环境极其不稳定，导致两次出现下载到一半（第 92、146 篇开始）时连接中断。

**解决方法**：

在代码中引入**基于文件存在性检查的断点续传逻辑**。在执行下载前，先校验本地是否已存在该文件且大小是否正常。

Python

```
# 关键代码：断点续传判断
if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
    print(f"{arxiv_id} 已存在且完整，跳过。")
    continue
```

![67afefb4570ab156d581c5438da780c3](C:\Users\门大开\xwechat_files\wxid_0vfnva4kjvx432_4317\temp\RWTemp\2026-03\67afefb4570ab156d581c5438da780c3.png)
### (3) 官方库失效，回归直接下载方案

**问题**：**第二次尝试从第 146 篇继续下载**时（第一次尝试时，从92篇开始正常下载了），官方库 `download_pdf()` 频繁报错。后来**查看官方文档**发现，官方库在下载前会额外请求一次 API 校验，导致 API 请求频率超标。

**解决方法**：

改为 **`urllib` 直接下载方案**。绕过 API 接口，直接根据 `arxiv_id` 拼接 PDF 存储服务器的静态 URL。配合 `random.uniform(8, 15)` 的随机退避延时，模拟人类低频下载行为，最终补齐 200 篇 PDF。

 ![e745cdc5699c578e4e6c47b737db4d3c](C:\Users\门大开\xwechat_files\wxid_0vfnva4kjvx432_4317\temp\RWTemp\2026-03\e745cdc5699c578e4e6c47b737db4d3c.png)


### (4) pdf转txt遇到学术排版问题

**问题**：初步使用 `pdf_to_txt` 提取时，双栏排版导致文字左右混杂，且出现了大量类似 `spe- cialized` 的断词。

**解决方法**：

选用目前社区最佳解决方案 **`PyMuPDF (fitz)`**，不再使用简单的文本提取，而是采用 **`blocks` 模式**并配合**坐标排序 (`sort=True`)**。同时利用正则表达式修复断词，并过滤掉物理尺寸过小的图表噪音。

Python

```
# 关键代码：修复连字符断词与块排序
blocks = page.get_text("blocks", sort=True)
text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', raw_text)
```

------

## 4. 抓取数据展示

- **papers.json**：严格包含**`arxiv_id`, `title`, `abstract`, `pdf_path`, `txt_path` **等核心字段 。

  ![image-20260327120921046](C:\Users\门大开\AppData\Roaming\Typora\typora-user-images\image-20260327120921046.png)

  

- **文件存储**：`paper_pdf/` 与 `paper_txt/` 文件夹下的对应文件 。
  ![image-20260327120838705](C:\Users\门大开\AppData\Roaming\Typora\typora-user-images\image-20260327120838705.png)

  ![image-20260327120803078](C:\Users\门大开\AppData\Roaming\Typora\typora-user-images\image-20260327120803078.png)

  ![image-20260327120722468](C:\Users\门大开\AppData\Roaming\Typora\typora-user-images\image-20260327120722468.png)

  

------

### 5. 参考文献与学习资料

1. **arXiv API User's Manual**（arXiv的官方API接口文档）
2. **PyMuPDF (fitz) Documentation** （PyMuPDF库文档）
3. Python `arxiv` library documentation 