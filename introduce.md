你是一位精通大模型（LLM）应用开发、数据分析与 Streamlit 前端微服务搭建的高级全栈算法工程师。现在我需要你扮演我的结对编程伙伴，帮我从零编写一个可以直接运行的完整项目。

这个项目是为了准备米哈游（miHoYo）的“市场内容及舆情分析实习生（AI技术应用方向）”岗位而设计的。我们需要在一个单文件或简单的项目结构中，实现基于 AnySearch API 的真实数据抓取、大模型 API 调用、非结构化文本清洗打标、爆点预测，以及一个包含交互与可视化的 Streamlit 看板。

请严格按照以下模块和要求，直接输出生产环境级别的、有详尽中文注释的 Python 代码。

---

### 一、 项目核心功能模块

1. **数据采集模块 (Data Scraping via AnySearch API)**：
   - 编写一个真实的数据抓取函数，调用 AnySearch API（官方网站参考：https://www.anysearch.com/home ）来获取游戏相关的社媒舆情数据。
   - 代码中需使用 `requests` 或 `httpx` 实现标准的 API 调用逻辑，并支持从环境变量或配置文件中读取 `ANYSEARCH_API_KEY`。
   - 函数需支持传入特定的搜索关键词（如：“Genshin Impact bug”, “Honkai Star Rail character review”），并解析 API 返回的 JSON，提取出：发帖时间、网页/评论内容、作者或来源平台、URL 等核心字段，最终组装为 `pandas.DataFrame`。

2. **LLM 自动化清洗与多维度打标模块 (LLM Processing Pipeline)**：
   - 使用 Python 调用大模型 API（请使用标准的 OpenAI SDK 格式，以便于后续切换 OpenAI/DeepSeek 接口）。
   - 设计一个严谨的 Prompt，输入 AnySearch 抓取到的原始文本，让大模型输出标准的 JSON 格式，包含以下字段：
     * `clean_text`: 清洗掉 HTML 标签、无意义字符后的核心文本。
     * `language`: 语言类型。
     * `sentiment`: 情感倾向（正向/中性/负向）。
     * `category`: 内容分类（如：角色设计、玩法吐槽、同人二创、Bug反馈、运营活动）。
     * `keywords`: 关键词列表（最多3个）。
     * `is_viral_potential`: 是否具备爆点或引发大范围舆情的潜力（布尔值）。

3. **内容爆点总结与舆情预测模块 (Insight & Summary)**：
   - 编写一个聚合分析函数，将打标后的 DataFrame 传入，利用大模型对低评分/高热度/高潜力的舆情进行总结，生成一份结构化的 Markdown 格式舆情分析简报，包括：核心痛点提炼、竞品或玩家动态摘要。

4. **Streamlit 交互看板模块 (Dashboard Interface)**：
   - 搭建一个 Web 界面，包含：
     * **Sidebar（侧边栏）**：配置 AnySearch API Key、LLM API Key、模型选择、搜索关键词输入框及“开始抓取与分析”按钮。
     * **Tab 1: 实时抓取与打标**：展示从 AnySearch 获取的原始数据；调用 LLM 时展示进度条（`st.progress`）；处理完成后用 `st.dataframe` 展示完整的打标结果，并提供 CSV 下载。
     * **Tab 2: 舆情统计图表**：使用 Streamlit 原生图表或 Altair/Plotly 展示情感倾向的饼图/柱状图、不同内容分类的数量分布。
     * **Tab 3: AI 舆情简报**：渲染大模型生成的 Markdown 舆情总结报告，并使用 `st.warning` 或 `st.error` 高亮显示需要干预的负面爆点。

---

### 二、 代码编写严格要求

1. **严禁伪代码**：所有代码必须完整。必须包含异常处理机制（如 AnySearch API 调用失败、LLM 请求超时、JSON 解析失败的兜底逻辑）。
2. **异步或批量处理优化**：调用大模型 API 对多条文本进行打标时，必须使用并发（如 `concurrent.futures.ThreadPoolExecutor`）加速处理。
3. **结构化输出稳定性**：大模型返回 JSON 时可能带有 ```json ``` 代码块标记，请编写健壮的提取与解析逻辑，避免因解析报错导致程序中断。
4. **视觉与排版**：Streamlit 界面需布局合理，善用 `st.columns`、`st.metric` 提升业务看板的专业感。

---

### 三、 期望的输出格式

请直接给出：
1. **`requirements.txt`**：列出项目依赖的所有库（需包含 requests, pandas, streamlit, openai 等）。
2. **`app.py`**：完整的、一键可运行的 Python 源码。
3. **运行指南**：简要说明如何配置 API Key 环境变量并启动项目。