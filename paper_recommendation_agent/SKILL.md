
---

# SKILL.md: Arxiv Scholar Pipeline

## 1. 技能概述 (Overview)

**名称**: Arxiv Scholar Pipeline (Arxiv 学术流水线)
**描述**: 一个高鲁棒性的自动化数据采集智能体。它负责执行从元数据爬取、双重保障下载 PDF、到最终文本提取的完整 ETL (Extract-Transform-Load) 流程。
**核心策略**:
1.  **元数据优先**: 先获取 `papers.json`。
2.  **分级下载**: 优先使用官方 API (`download_pdf_arXiv.py`)，随后自动切换到底层直连 (`download_pdf_urllib.py`) 进行补漏，确保 100% 下载率。
3.  **智能清洗**: 使用 `PyMuPDF` 处理双栏排版和断词问题。

## 2. 前置检查与环境修复 (Pre-flight Checks)
在执行任何 Python 脚本前，必须执行以下检查和修复步骤，以确保环境可用性：

1.  **依赖检查**: 确认已安装 `arxiv`, `PyMuPDF` (fitz)。
    *   *Command*: `pip install arxiv PyMuPDF`
2.  **代码健壮性修复 (Critical Fix)**:
    *   检测到提供的脚本中入口函数写法为 `if name == "main":`，这在 Python 中是无效的（应为 `if __name__ == "__main__":`）。
    *   *Action*: 在运行前，自动使用 sed 或文本替换工具修复所有 `.py` 文件中的这一行，或者在调用时显式指定函数（不推荐），**建议优先修复代码**。
    *   *Fix Command*:
        ```powershell
        (Get-Content crawler.py) -replace 'if name == "main":', 'if __name__ == "__main__":' | Set-Content crawler.py
        # 对其他三个文件重复此操作
        ```

## 3. 执行工作流 (Execution Workflow)

请严格按照以下顺序执行步骤。每一步完成后，必须验证输出文件是否存在且有效，才能进入下一步。

### 阶段一：元数据爬取 (Metadata Extraction)
*   **目标**: 生成包含 200 篇论文信息的 `papers.json`。
*   **脚本**: `crawler.py`
*   **执行逻辑**:
    1.  运行 `python crawler.py`。
    2.  **验证**: 检查 `papers.json` 是否存在。
    3.  **验证**: 读取 JSON，确认 `len(papers)` 是否接近 200（允许少量网络波动，但应 > 180）。
    4.  *异常处理*: 如果 JSON 为空或不存在，检查网络连接或 API 配额，重试一次。

### 阶段二：主通道 PDF 下载 (Primary Download)
*   **目标**: 下载大部分 PDF 文件。
*   **脚本**: `download_pdf_arXiv.py`
*   **执行逻辑**:
    1.  运行 `python download_pdf_arXiv.py`。
    2.  该脚本使用官方库，速度较慢但元数据匹配度高。
    3.  **注意**: 该脚本内置了断点续传逻辑，如果中途停止，再次运行会自动跳过已下载文件。

### 阶段三：补漏下载 (Fallback Download)
*   **目标**: 解决 429 错误或官方库下载失败的问题，补齐剩余 PDF。
*   **脚本**: `download_pdf_urllib.py`
*   **执行逻辑**:
    1.  运行 `python download_pdf_urllib.py`。
    2.  **原理**: 该脚本直接请求 `arxiv.org/pdf/{id}.pdf`，绕过 API 限制。
    3.  **验证**: 检查 `paper_pdf/` 文件夹。统计 `.pdf` 文件数量。
    4.  **目标**: 确保 PDF 数量与 `papers.json` 中的条目数量一致。

### 阶段四：文本提取与清洗 (Text Extraction)
*   **目标**: 将 PDF 转换为可读的 TXT，修复双栏排版。
*   **脚本**: `pdf_to_txt.py`
*   **执行逻辑**:
    1.  运行 `python pdf_to_txt.py`。
    2.  该脚本使用 `sort=True` 处理双栏，并用正则修复断词（如 `struc- \n tured` -> `structured`）。
    3.  **验证**: 检查 `paper_txt/` 文件夹。
    4.  **最终报告**: 输出成功转换的文件数量。

## 4. 最终交付物检查 (Final Deliverables)
任务完成后，请向用户汇报以下统计信息：
1.  **JSON 记录数**: `papers.json` 中的论文总数。
2.  **PDF 下载数**: `paper_pdf/` 中的文件数。
3.  **TXT 转换数**: `paper_txt/` 中的文件数。
4.  **完整性评分**: (TXT 数量 / JSON 数量) * 100%。

---

## 5. 开发者备注 (Developer Notes)
*   **关于两个下载脚本**: 这是一个典型的 "Retry with different strategy" 模式。`arXiv` 脚本负责稳健，`urllib` 脚本负责暴力补漏。不要跳过任何一个。
*   **关于路径**: 所有路径均相对于当前工作目录。确保在 `C:\Users\门大开\Desktop\大三下\周五_信息检索与人工智能\作业二` 下运行。
*   **关于编码**: 所有 JSON 操作均使用 `utf-8`，确保中文字符不报错。

---

