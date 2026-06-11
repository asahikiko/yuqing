# 米哈游社媒舆情 AI 分析台

这是一个面向“市场内容及舆情分析实习生（AI 技术应用方向）”岗位准备的 Streamlit 项目，支持使用 AnySearch 获取游戏相关实时搜索结果，再通过 OpenAI SDK 兼容接口完成文本清洗、多维打标、爆点预测和 AI 舆情简报生成。

参考资料：

- AnySearch Skill GitHub：https://github.com/anysearch-ai/anysearch-skill
- AnySearch 官网：https://www.anysearch.com/home

## 功能亮点

- 通过 `requests` 调用 AnySearch JSON-RPC MCP 接口：`https://api.anysearch.com/mcp`
- 支持 `ANYSEARCH_API_KEY`，未配置时可匿名访问，但会受到更低额度限制
- 使用 OpenAI SDK 兼容格式接入 OpenAI、DeepSeek 或其他兼容服务
- 使用 `ThreadPoolExecutor` 对多条内容并发打标
- 健壮解析 LLM 返回 JSON，兼容 ```json 代码块
- Streamlit 三页签看板：实时抓取与打标、舆情统计图表、AI 舆情简报
- 使用 Plotly 展示情感倾向、内容分类和风险等级

## 安装依赖

```powershell
pip install -r requirements.txt
```

## 配置 API Key

PowerShell 临时环境变量：

```powershell
$env:ANYSEARCH_API_KEY="你的 AnySearch API Key"
$env:OPENAI_API_KEY="你的 LLM API Key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_MODEL="gpt-4o-mini"
```

如果使用 DeepSeek 等 OpenAI SDK 兼容接口，可以把 `OPENAI_BASE_URL` 和 `OPENAI_MODEL` 改成对应服务提供的值。

## 启动项目

```powershell
streamlit run app.py
```

启动后在侧边栏填写或确认：

- AnySearch API Key
- LLM API Key
- LLM Base URL
- 模型名称
- 搜索关键词
- AnySearch 检索领域

然后点击“开始抓取与分析”。

## 文件说明

- `requirements.txt`：项目依赖
- `app.py`：完整 Streamlit 应用源码
- `README.md`：运行指南
