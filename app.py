import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

ANYSEARCH_ENDPOINT = "https://api.anysearch.com/mcp"
DEFAULT_LLM_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://hk.uniapi.io/v1")
DEFAULT_LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
RECENT_DAYS = 15


st.set_page_config(
    page_title="米哈游社媒舆情 AI 分析台",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_page_style() -> None:
    """为 Streamlit 页面注入更接近业务看板的视觉风格。"""
    st.markdown(
        """
        <style>
        :root {
            --brand-blue: #72E4FF;
            --brand-purple: #B88CFF;
            --brand-pink: #FF8AC7;
            --brand-gold: #FFD166;
            --panel-bg: rgba(8, 13, 28, 0.72);
        }

        .stApp {
            background:
                radial-gradient(circle at 18% 8%, rgba(114, 228, 255, 0.22), transparent 28%),
                radial-gradient(circle at 88% 10%, rgba(255, 138, 199, 0.18), transparent 26%),
                radial-gradient(circle at 50% 92%, rgba(184, 140, 255, 0.18), transparent 30%),
                linear-gradient(135deg, #060B19 0%, #0B1024 42%, #171022 100%);
            color: #EEF4FF;
        }

        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1380px;
        }

        .hero-card {
            position: relative;
            overflow: hidden;
            padding: 2.4rem 2.5rem;
            border-radius: 34px;
            border: 1px solid rgba(226, 232, 240, 0.18);
            background:
                linear-gradient(135deg, rgba(114, 228, 255, 0.20), rgba(184, 140, 255, 0.16) 45%, rgba(255, 138, 199, 0.13)),
                rgba(8, 13, 28, 0.74);
            box-shadow: 0 28px 90px rgba(0, 0, 0, 0.42);
            margin-bottom: 1.15rem;
            backdrop-filter: blur(18px);
        }

        .hero-card:before {
            content: "";
            position: absolute;
            width: 360px;
            height: 360px;
            right: -110px;
            top: -160px;
            background: radial-gradient(circle, rgba(255, 209, 102, 0.24), transparent 62%);
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.38rem 0.72rem;
            border-radius: 999px;
            color: #CFFAFE;
            background: rgba(14, 165, 233, 0.13);
            border: 1px solid rgba(125, 211, 252, 0.22);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.95rem;
        }

        .hero-title {
            position: relative;
            font-size: clamp(2.25rem, 5vw, 4.25rem);
            line-height: 1.03;
            font-weight: 900;
            letter-spacing: -0.06em;
            margin-bottom: 0.8rem;
            color: #FFFFFF;
        }

        .hero-subtitle {
            position: relative;
            color: #D8E5F8;
            font-size: 1.05rem;
            line-height: 1.8;
            max-width: 1040px;
        }

        .badge-row {
            display: flex;
            gap: 0.65rem;
            flex-wrap: wrap;
            margin-top: 1.05rem;
        }

        .soft-badge {
            border-radius: 999px;
            padding: 0.48rem 0.78rem;
            border: 1px solid rgba(226, 232, 240, 0.18);
            background: rgba(2, 6, 23, 0.42);
            color: #E5F4FF;
            font-size: 0.86rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }

        .section-card {
            padding: 1.2rem 1.25rem;
            border-radius: 24px;
            border: 1px solid rgba(148, 163, 184, 0.20);
            background: rgba(8, 13, 28, 0.62);
            margin-bottom: 1rem;
            box-shadow: 0 18px 55px rgba(0, 0, 0, 0.22);
            backdrop-filter: blur(16px);
        }

        .control-card {
            padding: 1.35rem 1.45rem 1.45rem;
            border-radius: 28px;
            border: 1px solid rgba(226, 232, 240, 0.18);
            background:
                linear-gradient(135deg, rgba(14, 165, 233, 0.13), rgba(139, 92, 246, 0.12)),
                rgba(8, 13, 28, 0.70);
            box-shadow: 0 22px 70px rgba(0, 0, 0, 0.28);
            margin-bottom: 1rem;
        }

        .control-title {
            color: #FFFFFF;
            font-size: 1.22rem;
            font-weight: 860;
            margin-bottom: 0.35rem;
        }

        .control-desc {
            color: #C9D8EA;
            font-size: 0.92rem;
            line-height: 1.7;
            margin-bottom: 0.75rem;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
            margin: 0.95rem 0 1.15rem;
        }

        .status-card {
            border-radius: 22px;
            padding: 1rem 1.05rem;
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.70), rgba(2, 6, 23, 0.44));
            border: 1px solid rgba(148, 163, 184, 0.18);
        }

        .status-label {
            color: #93A4B8;
            font-size: 0.78rem;
            margin-bottom: 0.28rem;
        }

        .status-value {
            color: #F8FBFF;
            font-size: 1rem;
            font-weight: 800;
        }

        .sidebar-status {
            padding: 0.95rem 1rem;
            border-radius: 20px;
            background:
                linear-gradient(135deg, rgba(20, 184, 166, 0.12), rgba(59, 130, 246, 0.10)),
                rgba(2, 6, 23, 0.34);
            border: 1px solid rgba(125, 211, 252, 0.18);
            margin: 0.65rem 0 1rem;
        }

        .sidebar-status-title {
            font-weight: 800;
            color: #F8FBFF;
            margin-bottom: 0.35rem;
        }

        .sidebar-status-line {
            color: #C7D2FE;
            font-size: 0.86rem;
            line-height: 1.8;
        }

        div[data-testid="stMetric"] {
            padding: 1rem 1.05rem;
            border-radius: 22px;
            border: 1px solid rgba(148, 163, 184, 0.20);
            background:
                linear-gradient(180deg, rgba(15, 23, 42, 0.72), rgba(2, 6, 23, 0.42));
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.20);
        }

        div[data-testid="stTabs"] button {
            color: #E7F0FF;
            font-weight: 650;
        }

        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
            border-radius: 18px;
            border: 1px solid rgba(125, 211, 252, 0.28);
            background: linear-gradient(135deg, #38BDF8, #8B5CF6);
            color: white;
            font-weight: 800;
            box-shadow: 0 16px 34px rgba(56, 189, 248, 0.18);
        }

        .stFormSubmitButton > button {
            min-height: 3.1rem;
            font-size: 1.02rem;
            letter-spacing: 0.02em;
        }

        .stDataFrame {
            border-radius: 20px;
            overflow: hidden;
        }

        @media (max-width: 900px) {
            .status-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_runtime_config(name: str, default: str = "") -> str:
    """从环境变量或 Streamlit secrets 读取配置，避免在页面暴露密钥。"""
    env_value = os.getenv(name, "")
    if env_value:
        return env_value
    try:
        secret_value = st.secrets.get(name, "")
    except Exception:
        secret_value = ""
    return str(secret_value or default)


def normalize_base_url(base_url: str) -> str:
    cleaned = base_url.strip().rstrip("/")
    if cleaned == "https://hk.uniapi.io":
        return "https://hk.uniapi.io/v1"
    return cleaned


def get_recent_window() -> Dict[str, str]:
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=RECENT_DAYS)
    return {
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "label": f"{start_date.isoformat()} 至 {end_date.isoformat()}",
    }


def build_recent_search_query(query: str) -> str:
    window = get_recent_window()
    return (
        f"{query} recent game community discussion published between "
        f"{window['start']} and {window['end']} only, last {RECENT_DAYS} days"
    )


def build_anysearch_headers(api_key: str) -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def call_anysearch_search(
    query: str,
    api_key: str,
    max_results: int = 8,
    domain: str = "gaming",
    timeout: int = 35,
) -> Dict[str, Any]:
    """
    调用 AnySearch 的 JSON-RPC MCP 接口。

    AnySearch 官方 Skill 使用 tools/call + search 工具完成搜索，这里直接用 requests
    复刻标准 API 调用，便于在项目中部署和调试。
    """
    recent_query = build_recent_search_query(query)
    arguments: Dict[str, Any] = {
        "query": recent_query,
        "max_results": min(max(int(max_results), 1), 10),
    }
    if domain:
        arguments["domain"] = domain

    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {"name": "search", "arguments": arguments},
    }

    response = requests.post(
        ANYSEARCH_ENDPOINT,
        json=payload,
        headers=build_anysearch_headers(api_key),
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        message = data["error"].get("message", str(data["error"]))
        raise RuntimeError(f"AnySearch API Error: {message}")
    return data


def get_text_from_anysearch_response(data: Dict[str, Any]) -> str:
    result = data.get("result", {})
    content = result.get("content", [])
    if isinstance(content, list):
        text_blocks = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return "\n\n".join(block for block in text_blocks if block)
    return json.dumps(result, ensure_ascii=False)


def extract_first_json(raw_text: str) -> Optional[Any]:
    """兼容模型或搜索接口返回 ```json ... ``` 与普通 JSON 文本的情况。"""
    if not raw_text:
        return None

    text = raw_text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    candidates = [text]
    object_match = re.search(r"(\{[\s\S]*\})", text)
    array_match = re.search(r"(\[[\s\S]*\])", text)
    if array_match:
        candidates.append(array_match.group(1))
    if object_match:
        candidates.append(object_match.group(1))

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def walk_json_items(value: Any) -> Iterable[Dict[str, Any]]:
    """从未知 JSON 结构中递归提取搜索结果对象。"""
    if isinstance(value, dict):
        has_content = any(
            key in value
            for key in (
                "title",
                "url",
                "link",
                "snippet",
                "content",
                "text",
                "source",
                "published_at",
                "date",
            )
        )
        if has_content:
            yield value
        for child in value.values():
            yield from walk_json_items(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json_items(child)


def normalize_result_item(item: Dict[str, Any], query: str) -> Dict[str, Any]:
    title = str(item.get("title") or item.get("name") or item.get("headline") or "").strip()
    url = str(item.get("url") or item.get("link") or item.get("href") or "").strip()
    content = str(
        item.get("content")
        or item.get("snippet")
        or item.get("summary")
        or item.get("description")
        or item.get("text")
        or ""
    ).strip()
    source = str(
        item.get("source")
        or item.get("site")
        or item.get("platform")
        or item.get("author")
        or item.get("domain")
        or "AnySearch"
    ).strip()
    published_at = str(
        item.get("published_at")
        or item.get("publishedTime")
        or item.get("created_at")
        or item.get("date")
        or item.get("time")
        or ""
    ).strip()

    if not content and title:
        content = title

    return {
        "query": query,
        "published_at": published_at,
        "title": title or content[:36],
        "content": content,
        "source": source,
        "url": url,
    }


def parse_markdown_search_results(markdown_text: str, query: str) -> List[Dict[str, Any]]:
    """
    当 AnySearch 返回 Markdown 文本时，尽量从标题链接和片段中恢复结构化记录。
    这不是伪造数据，只是对 API 文本结果做保守解析。
    """
    rows: List[Dict[str, Any]] = []
    blocks = [block.strip() for block in re.split(r"\n\s*\n", markdown_text) if block.strip()]

    for block in blocks:
        link_match = re.search(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", block)
        raw_url_match = re.search(r"(https?://[^\s)]+)", block)
        if not link_match and not raw_url_match:
            continue

        title = link_match.group(1).strip() if link_match else block.splitlines()[0].strip("# -* ")
        url = link_match.group(2).strip() if link_match else raw_url_match.group(1).strip()
        clean_lines = []
        for line in block.splitlines():
            line = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r"\1", line).strip(" -*")
            if line and line != title:
                clean_lines.append(line)
        content = " ".join(clean_lines).strip() or title
        source = re.sub(r"^www\.", "", re.sub(r"https?://", "", url).split("/")[0])

        rows.append(
            {
                "query": query,
                "published_at": "",
                "title": title,
                "content": content,
                "source": source or "AnySearch",
                "url": url,
            }
        )

    return rows


def parse_anysearch_response(data: Dict[str, Any], query: str) -> pd.DataFrame:
    raw_text = get_text_from_anysearch_response(data)
    parsed_json = extract_first_json(raw_text)

    rows: List[Dict[str, Any]] = []
    if parsed_json is not None:
        rows = [normalize_result_item(item, query) for item in walk_json_items(parsed_json)]

    if not rows:
        rows = parse_markdown_search_results(raw_text, query)

    if not rows and raw_text:
        rows = [
            {
                "query": query,
                "published_at": "",
                "title": query,
                "content": raw_text[:2000],
                "source": "AnySearch",
                "url": "",
            }
        ]

    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return pd.DataFrame(columns=["query", "published_at", "title", "content", "source", "url"])
    return dataframe.drop_duplicates(subset=["url", "content"]).reset_index(drop=True)


def fetch_social_media_data(
    keywords: List[str],
    api_key: str,
    max_results_per_keyword: int,
    domain: str,
) -> pd.DataFrame:
    all_frames: List[pd.DataFrame] = []
    errors: List[str] = []

    for keyword in keywords:
        try:
            data = call_anysearch_search(
                query=keyword,
                api_key=api_key,
                max_results=max_results_per_keyword,
                domain=domain,
            )
            frame = parse_anysearch_response(data, keyword)
            all_frames.append(frame)
        except requests.exceptions.Timeout:
            errors.append(f"关键词「{keyword}」请求超时")
        except requests.exceptions.HTTPError as exc:
            errors.append(f"关键词「{keyword}」HTTP 请求失败：{exc}")
        except Exception as exc:
            errors.append(f"关键词「{keyword}」处理失败：{exc}")

    if errors:
        st.warning("；".join(errors))

    if not all_frames:
        return pd.DataFrame(columns=["query", "published_at", "title", "content", "source", "url"])
    return pd.concat(all_frames, ignore_index=True).drop_duplicates(subset=["url", "content"])


def build_llm_client(api_key: str, base_url: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url=base_url, timeout=45)


def build_tagging_prompt(row: pd.Series) -> str:
    window = get_recent_window()
    return f"""
你是米哈游市场内容与舆情分析实习生的 AI 助手，擅长判断游戏社区内容的传播风险。
请只返回一个合法 JSON 对象，不要返回解释文字。

硬性时间要求：
- 本系统只分析最近 {RECENT_DAYS} 天内的信息，时间范围为 {window["label"]}。
- 如果原文时间明显早于该范围，请在 action_suggestion 中明确提示“疑似旧信息，需人工复核”，并把 risk_level 降为 low。
- 如果原文没有明确发布时间，请基于内容中的版本、活动、讨论语境判断时效性，并在建议中提示需要核验时间。

需要分析的搜索关键词：{row.get("query", "")}
来源平台/站点：{row.get("source", "")}
标题：{row.get("title", "")}
发布时间：{row.get("published_at", "")}
原始文本：
{row.get("content", "")}

JSON 字段要求：
- clean_text: 清洗 HTML、广告噪声、重复字符后的核心中文或原文文本。
- language: 语言类型，如 zh/en/ja/ko/mixed/unknown。
- sentiment: 只能是 正向 / 中性 / 负向。
- category: 只能从 角色设计、玩法吐槽、同人二创、Bug反馈、运营活动、版本更新、抽卡消费、竞品动态、其他 中选择。
- keywords: 字符串数组，最多 3 个关键词。
- is_viral_potential: 布尔值，判断是否可能形成爆点或大范围舆情。
- risk_level: 只能是 low / medium / high。
- action_suggestion: 给运营或市场同学的一句话处理建议。
"""


def default_tagging_result(row: pd.Series, error: str = "") -> Dict[str, Any]:
    content = str(row.get("content", "") or "")
    return {
        "clean_text": re.sub(r"\s+", " ", content).strip()[:600],
        "language": "unknown",
        "sentiment": "中性",
        "category": "其他",
        "keywords": [],
        "is_viral_potential": False,
        "risk_level": "low",
        "action_suggestion": "建议人工复核该条内容。",
        "llm_error": error,
    }


def analyze_single_row(
    row: pd.Series,
    api_key: str,
    base_url: str,
    model: str,
) -> Dict[str, Any]:
    if not api_key:
        return default_tagging_result(row, "未配置 LLM API Key")

    try:
        client = build_llm_client(api_key=api_key, base_url=base_url)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "你是严谨的游戏舆情分析专家，所有回答必须是可解析 JSON。",
                },
                {"role": "user", "content": build_tagging_prompt(row)},
            ],
        )
        raw_content = completion.choices[0].message.content or "{}"
        parsed = extract_first_json(raw_content)
        if not isinstance(parsed, dict):
            raise ValueError("LLM 返回内容不是 JSON 对象")

        result = default_tagging_result(row)
        result.update(parsed)
        if not isinstance(result.get("keywords"), list):
            result["keywords"] = [str(result["keywords"])]
        result["keywords"] = result["keywords"][:3]
        result["is_viral_potential"] = bool(result.get("is_viral_potential"))
        result["llm_error"] = ""
        return result
    except Exception as exc:
        return default_tagging_result(row, str(exc))


def tag_dataframe_with_llm(
    dataframe: pd.DataFrame,
    api_key: str,
    base_url: str,
    model: str,
    max_workers: int,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    results: List[Optional[Dict[str, Any]]] = [None] * len(dataframe)
    progress = st.progress(0, text="正在调用大模型进行清洗与多维打标...")
    status = st.empty()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(analyze_single_row, row, api_key, base_url, model): index
            for index, row in dataframe.iterrows()
        }
        finished = 0
        for future in as_completed(future_map):
            index = future_map[future]
            results[index] = future.result()
            finished += 1
            progress.progress(
                finished / len(dataframe),
                text=f"已完成 {finished}/{len(dataframe)} 条内容打标",
            )
            status.caption(f"当前处理进度：{finished}/{len(dataframe)}")

    progress.empty()
    status.empty()

    tag_frame = pd.DataFrame(results)
    merged = pd.concat([dataframe.reset_index(drop=True), tag_frame], axis=1)
    merged["keywords"] = merged["keywords"].apply(
        lambda value: "、".join(map(str, value)) if isinstance(value, list) else str(value)
    )
    return merged


def build_summary_prompt(tagged_df: pd.DataFrame) -> str:
    window = get_recent_window()
    important_columns = [
        "query",
        "title",
        "source",
        "clean_text",
        "sentiment",
        "category",
        "keywords",
        "is_viral_potential",
        "risk_level",
        "action_suggestion",
        "url",
    ]
    compact_records = tagged_df[important_columns].head(40).to_dict(orient="records")
    return f"""
你是米哈游市场内容及舆情分析实习生（AI 技术应用方向）的候选人，需要基于社媒抓取结果生成一份专业 Markdown 舆情简报。

硬性时间要求：本简报只允许总结最近 {RECENT_DAYS} 天内的信息，时间范围为 {window["label"]}。若数据中存在疑似旧信息或无法判断发布时间的内容，必须单独标注“需核验时效”，不要把它当作确定趋势。

请输出结构化 Markdown，包含：
1. 执行摘要：3-5 条最高优先级发现。
2. 核心痛点提炼：按 Bug反馈、玩法吐槽、角色设计、抽卡消费、运营活动、竞品动态等维度归纳。
3. 爆点预测：列出可能发酵的议题、触发原因、风险等级、建议动作。
4. 玩家与竞品动态：提炼社区情绪与可借鉴的内容机会。
5. 运营建议：给内容、社区、产品同学可执行的下一步。

请避免空泛表达，尽量引用来源平台、关键词和具体问题。

数据如下：
{json.dumps(compact_records, ensure_ascii=False, indent=2)}
"""


def generate_insight_report(
    tagged_df: pd.DataFrame,
    api_key: str,
    base_url: str,
    model: str,
) -> str:
    if tagged_df.empty:
        return "暂无可分析数据。"
    if not api_key:
        return "未配置 LLM API Key，无法生成 AI 舆情简报。请在后端环境变量或 Streamlit secrets 中配置后重新分析。"

    try:
        client = build_llm_client(api_key=api_key, base_url=base_url)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.25,
            messages=[
                {
                    "role": "system",
                    "content": "你是游戏行业资深舆情分析师，输出专业、具体、可执行的中文 Markdown 简报。",
                },
                {"role": "user", "content": build_summary_prompt(tagged_df)},
            ],
        )
        return completion.choices[0].message.content or "模型未返回简报内容。"
    except Exception as exc:
        return f"生成简报失败：{exc}"


def build_statistics_summary_prompt(tagged_df: pd.DataFrame) -> str:
    window = get_recent_window()
    summary_payload = {
        "time_window": window["label"],
        "total": int(len(tagged_df)),
        "sentiment": tagged_df["sentiment"].fillna("未知").value_counts().to_dict(),
        "category": tagged_df["category"].fillna("其他").value_counts().head(8).to_dict(),
        "risk": tagged_df["risk_level"].fillna("low").value_counts().to_dict(),
        "viral_count": int(tagged_df["is_viral_potential"].fillna(False).sum()),
        "top_examples": tagged_df[
            [
                "title",
                "source",
                "sentiment",
                "category",
                "risk_level",
                "keywords",
                "action_suggestion",
            ]
        ]
        .head(10)
        .to_dict(orient="records"),
    }
    return f"""
请基于下面的舆情统计结果，写一段简短、精要、适合放在数据看板顶部的中文总结。

要求：
- 只总结最近 {RECENT_DAYS} 天信息，时间范围：{window["label"]}。
- 2 到 4 句话即可。
- 重点说明当前整体情绪、主要议题、是否存在需要关注的风险。
- 不要暴露接口、模型、API 等技术细节。

统计数据：
{json.dumps(summary_payload, ensure_ascii=False, indent=2)}
"""


def generate_statistics_summary(
    tagged_df: pd.DataFrame,
    api_key: str,
    base_url: str,
    model: str,
) -> str:
    if tagged_df.empty:
        return "暂无可总结数据。完成一次抓取与分析后，这里会自动生成近期舆情概览。"
    if not api_key:
        return "智能分析能力未配置，暂时只能展示统计图表。"

    try:
        client = build_llm_client(api_key=api_key, base_url=base_url)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "你是游戏社区舆情看板的产品分析助手，回答简短、具体、业务化。",
                },
                {"role": "user", "content": build_statistics_summary_prompt(tagged_df)},
            ],
        )
        return completion.choices[0].message.content or "暂未生成统计总结。"
    except Exception as exc:
        return f"统计总结生成失败：{exc}"


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="eyebrow">Public Opinion Insight Dashboard</div>
            <div class="hero-title">米哈游社媒舆情<br/>AI 分析台</div>
            <div class="hero-subtitle">
                面向游戏社区与市场内容场景，自动聚合近期玩家讨论，识别情绪变化、集中痛点与潜在传播风险，
                帮助面试官快速看到候选人在数据采集、内容理解、分析总结和产品化呈现上的完整能力。
            </div>
            <div class="badge-row">
                <span class="soft-badge">优先最近15天动态</span>
                <span class="soft-badge">玩家情绪识别</span>
                <span class="soft-badge">热点议题归因</span>
                <span class="soft-badge">运营建议生成</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_control_panel() -> Dict[str, Any]:
    anysearch_api_key = get_runtime_config("ANYSEARCH_API_KEY")
    llm_api_key = get_runtime_config("OPENAI_API_KEY")
    llm_base_url = normalize_base_url(get_runtime_config("OPENAI_BASE_URL", DEFAULT_LLM_BASE_URL))
    llm_model = get_runtime_config("OPENAI_MODEL", DEFAULT_LLM_MODEL)

    default_keywords = "\n".join(
        [
            "Genshin Impact bug",
            "Honkai Star Rail character review",
            "Zenless Zone Zero event feedback",
            "miHoYo gacha complaints",
        ]
    )
    model_options = [
        llm_model,
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1-mini",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]
    model_options = list(dict.fromkeys([model for model in model_options if model]))
    window = get_recent_window()

    st.markdown(
        f"""
        <div class="control-card">
            <div class="control-title">启动一次新的舆情分析</div>
            <div class="control-desc">
                本次抓取会优先关注最近{RECENT_DAYS}天内（{window["label"]}）的社区反馈、活动舆论与风险议题。
                密钥由后端安全读取，页面不会展示任何 Key 明文。
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("analysis_control_form"):
        keywords_text = st.text_area(
            "关注关键词（每行一个）",
            value=default_keywords,
            height=118,
            help="建议覆盖游戏名、版本活动、角色、Bug、抽卡、竞品等方向。",
        )

        col1, col2, col3 = st.columns([1.15, 1, 1])
        with col1:
            domain = st.selectbox(
                "内容范围",
                ["gaming", "social_media", "general", "business", "film", "code"],
                index=0,
                format_func={
                    "gaming": "游戏社区",
                    "social_media": "社交媒体",
                    "general": "全网综合",
                    "business": "商业动态",
                    "film": "影音社区",
                    "code": "开发者社区",
                }.get,
            )
        with col2:
            max_results = st.slider("每个关键词结果数", 1, 10, 6)
        with col3:
            max_workers = st.slider("分析并发数", 1, 8, 4)

        selected_model = st.selectbox(
            "分析质量档位",
            model_options,
            index=0,
            help="默认档位已经过连通性验证，面试演示时一般无需调整。",
        )
        run_button = st.form_submit_button(
            f"开始抓取优先最近{RECENT_DAYS}天舆情并分析",
            type="primary",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    return {
        "anysearch_api_key": anysearch_api_key.strip(),
        "llm_api_key": llm_api_key.strip(),
        "llm_base_url": llm_base_url.strip(),
        "llm_model": selected_model.strip(),
        "keywords": [line.strip() for line in keywords_text.splitlines() if line.strip()],
        "domain": domain,
        "max_results": max_results,
        "max_workers": max_workers,
        "run_button": run_button,
    }


def render_metric_row(raw_df: pd.DataFrame, tagged_df: pd.DataFrame) -> None:
    total_count = len(raw_df)
    negative_count = int((tagged_df.get("sentiment", pd.Series(dtype=str)) == "负向").sum())
    viral_count = int(tagged_df.get("is_viral_potential", pd.Series(dtype=bool)).sum())
    high_risk_count = int((tagged_df.get("risk_level", pd.Series(dtype=str)) == "high").sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("抓取内容", total_count)
    col2.metric("负向内容", negative_count)
    col3.metric("潜在爆点", viral_count)
    col4.metric("高风险议题", high_risk_count)


def render_system_status(config: Dict[str, Any]) -> None:
    data_status = "可用" if config["anysearch_api_key"] else "基础可用"
    analysis_status = "已就绪" if config["llm_api_key"] else "待配置"
    window = get_recent_window()
    st.markdown(
        f"""
        <div class="status-grid">
            <div class="status-card">
                <div class="status-label">近期数据采集</div>
                <div class="status-value">{data_status}</div>
            </div>
            <div class="status-card">
                <div class="status-label">智能分析能力</div>
                <div class="status-value">{analysis_status}</div>
            </div>
            <div class="status-card">
                <div class="status-label">当前分析窗口</div>
                <div class="status-value">优先最近{RECENT_DAYS}天</div>
                <div class="status-label">{window["label"]}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_charts(tagged_df: pd.DataFrame) -> None:
    if tagged_df.empty:
        st.info("暂无打标数据，请先运行抓取与分析。")
        return

    col1, col2 = st.columns(2)

    sentiment_count = tagged_df["sentiment"].fillna("未知").value_counts().reset_index()
    sentiment_count.columns = ["sentiment", "count"]
    fig_sentiment = px.pie(
        sentiment_count,
        values="count",
        names="sentiment",
        hole=0.46,
        title="情感倾向占比",
        color_discrete_sequence=["#60A5FA", "#A78BFA", "#F87171", "#34D399"],
    )
    fig_sentiment.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    col1.plotly_chart(fig_sentiment, use_container_width=True)

    category_count = tagged_df["category"].fillna("其他").value_counts().reset_index()
    category_count.columns = ["category", "count"]
    fig_category = px.bar(
        category_count,
        x="category",
        y="count",
        title="内容分类分布",
        color="count",
        color_continuous_scale="Bluered",
    )
    fig_category.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    col2.plotly_chart(fig_category, use_container_width=True)

    risk_count = tagged_df["risk_level"].fillna("low").value_counts().reset_index()
    risk_count.columns = ["risk_level", "count"]
    fig_risk = px.bar(
        risk_count,
        x="risk_level",
        y="count",
        title="风险等级分布",
        color="risk_level",
        color_discrete_map={"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"},
    )
    fig_risk.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_risk, use_container_width=True)


def render_hot_issues(tagged_df: pd.DataFrame) -> None:
    if tagged_df.empty:
        return

    hot_df = tagged_df[
        (tagged_df["is_viral_potential"] == True)
        | (tagged_df["risk_level"].isin(["medium", "high"]))
        | (tagged_df["sentiment"] == "负向")
    ].copy()

    if hot_df.empty:
        st.success("当前结果中未发现明显负面爆点，建议持续监控高互动来源。")
        return

    st.error(f"发现 {len(hot_df)} 条需要优先关注的潜在舆情。")
    for _, row in hot_df.head(6).iterrows():
        with st.container(border=True):
            st.markdown(f"**{row.get('title', '未命名议题')}**")
            st.caption(
                f"来源：{row.get('source', '')}｜情感：{row.get('sentiment', '')}｜"
                f"分类：{row.get('category', '')}｜风险：{row.get('risk_level', '')}"
            )
            st.write(row.get("clean_text", row.get("content", "")))
            st.warning(row.get("action_suggestion", "建议人工复核。"))
            if row.get("url"):
                st.link_button("打开原文", row["url"])


def run_pipeline(config: Dict[str, Any]) -> None:
    if not config["keywords"]:
        st.warning("请至少输入一个搜索关键词。")
        return

    with st.spinner(f"正在优先抓取最近{RECENT_DAYS}天内的真实社区讨论..."):
        raw_df = fetch_social_media_data(
            keywords=config["keywords"],
            api_key=config["anysearch_api_key"],
            max_results_per_keyword=config["max_results"],
            domain=config["domain"],
        )

    if raw_df.empty:
        st.error("没有获取到可分析数据。请检查关键词、网络状态或后端数据源配置。")
        st.session_state["raw_df"] = raw_df
        st.session_state["tagged_df"] = raw_df
        st.session_state["stats_summary"] = "暂无可总结数据。"
        st.session_state["report"] = "暂无可分析数据。"
        return

    with st.spinner("正在并发调用大模型进行清洗、分类和爆点预测..."):
        tagged_df = tag_dataframe_with_llm(
            dataframe=raw_df,
            api_key=config["llm_api_key"],
            base_url=config["llm_base_url"],
            model=config["llm_model"],
            max_workers=config["max_workers"],
        )

    with st.spinner("正在生成统计页简短总结..."):
        stats_summary = generate_statistics_summary(
            tagged_df=tagged_df,
            api_key=config["llm_api_key"],
            base_url=config["llm_base_url"],
            model=config["llm_model"],
        )

    with st.spinner("正在生成 AI 舆情简报..."):
        report = generate_insight_report(
            tagged_df=tagged_df,
            api_key=config["llm_api_key"],
            base_url=config["llm_base_url"],
            model=config["llm_model"],
        )

    st.session_state["raw_df"] = raw_df
    st.session_state["tagged_df"] = tagged_df
    st.session_state["stats_summary"] = stats_summary
    st.session_state["report"] = report
    st.session_state["last_run_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    inject_page_style()
    render_hero()
    config = render_control_panel()
    render_system_status(config)

    if config["run_button"]:
        run_pipeline(config)

    raw_df = st.session_state.get("raw_df", pd.DataFrame())
    tagged_df = st.session_state.get("tagged_df", pd.DataFrame())
    stats_summary = st.session_state.get(
        "stats_summary",
        "完成一次抓取与分析后，这里会自动生成近期舆情概览。",
    )
    report = st.session_state.get("report", "点击上方按钮后生成 AI 舆情简报。")

    if "last_run_at" in st.session_state:
        st.caption(f"最近一次分析时间：{st.session_state['last_run_at']}")

    render_metric_row(raw_df, tagged_df)

    tab_stats, tab_raw, tab_report = st.tabs(["舆情统计图表", "实时抓取与打标", "AI 舆情简报"])

    with tab_stats:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("近期舆情概览")
        st.write(stats_summary)
        st.markdown("</div>", unsafe_allow_html=True)
        render_charts(tagged_df)

    with tab_raw:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("近期社区原始内容")
        if raw_df.empty:
            st.info("尚未抓取数据。")
        else:
            st.dataframe(raw_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("LLM 清洗与多维打标结果")
        if tagged_df.empty:
            st.info("尚未生成打标结果。")
        else:
            st.dataframe(tagged_df, use_container_width=True, hide_index=True)
            csv_data = tagged_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "下载打标结果 CSV",
                data=csv_data,
                file_name="mihoyo_social_sentiment_tags.csv",
                mime="text/csv",
                use_container_width=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_report:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("舆情简报")
        st.markdown(report)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        render_hot_issues(tagged_df)


if __name__ == "__main__":
    main()
