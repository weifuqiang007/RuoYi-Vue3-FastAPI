# utils/llm_json_parser.py
"""
LLM JSON 输出解析器
大模型偶尔返回带 markdown 代码块的文本或不合法 JSON，这个工具兼容各种格式
"""
import json
import re


def parse_llm_json(text: str) -> dict:
    """
    从 LLM 输出中提取 JSON，兼容各种格式：
    1. 直接 JSON
    2. ```json ... ``` 代码块
    3. 最外层 { } 匹配
    """
    if not text or not text.strip():
        raise ValueError("LLM 输出为空")

    text = text.strip()

    # 尝试 1：直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试 2：提取 ```json ... ``` 代码块
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试 3：找最外层 { }
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从 LLM 输出中提取 JSON，原文前200字: {text[:200]}")


def safe_parse_llm_json(text: str, default: dict = None) -> dict:
    """安全版本：解析失败返回 default 而不是抛异常"""
    try:
        return parse_llm_json(text)
    except Exception:
        return default or {}