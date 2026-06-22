# utils/llm_json_parser.py
"""
LLM JSON 输出解析器
大模型偶尔返回带 markdown 代码块的文本或不合法 JSON，这个工具兼容各种格式
"""
import json
import logging
import re

logger = logging.getLogger(__name__)


def _repair_truncated_json(text: str) -> str | None:
    """
    尽力修复被 max_tokens 截断的 JSON，返回修复后可被 json.loads 解析的字符串；无法保证合法则返回 None。

    策略：逐字符扫描，跟踪字符串上下文与括号栈，记录最后一个“结构完整边界”（逗号或闭合括号之后）。
    若检测到字符串未闭合或栈非空，判定为截断，分别尝试：
      - 候选1（保守）：回退到最后一个完整边界，丢弃尾部不完整的片段；
      - 候选2（激进）：保留全部文本，补上缺失的字符串结束引号。
    两个候选均去掉尾部悬挂的 , 或 :，并按栈补全闭合符号；任一能通过 json.loads 即返回。
    """
    start = text.find('{')
    if start == -1:
        return None
    body = text[start:]

    stack: list[str] = []          # 待闭合的 '{' 或 '['
    in_string = False
    escape = False
    last_complete_pos = 0          # 最后一个“结构完整边界”在 body 中的位置

    for idx, ch in enumerate(body):
        if escape:
            escape = False
            continue
        if in_string:
            if ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            stack.append('{')
        elif ch == '[':
            stack.append('[')
        elif ch == '}':
            if stack and stack[-1] == '{':
                stack.pop()
                last_complete_pos = idx + 1
        elif ch == ']':
            if stack and stack[-1] == '[':
                stack.pop()
                last_complete_pos = idx + 1
        elif ch == ',':
            last_complete_pos = idx + 1

    # 结构看似完整（栈空且不在字符串中）却仍被传入，说明不是截断问题，交回上层处理
    if not stack and not in_string:
        return None

    closing = ''.join('}' if o == '{' else ']' for o in reversed(stack))

    candidates: list[str] = []
    if last_complete_pos > 0:
        candidates.append(body[:last_complete_pos])        # 保守：丢弃尾部不完整片段
    full = body + ('"' if in_string else '')
    candidates.append(full)                                  # 激进：补字符串引号保留全部

    for cand in candidates:
        cand = cand.rstrip()
        while cand and cand[-1] in ',:':
            cand = cand[:-1].rstrip()
        repaired = cand + closing
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            continue
    return None


def parse_llm_json(text: str) -> dict:
    """
    从 LLM 输出中提取 JSON，兼容各种格式：
    1. 直接 JSON
    2. ```json ... ``` 代码块
    3. 最外层 { } 匹配
    4. 被 max_tokens 截断的 JSON 尽力修复
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

    # 尝试 4：被 max_tokens 截断的 JSON，尽力补全闭合符号修复
    repaired = _repair_truncated_json(text)
    if repaired is not None:
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    # 全部失败：记录完整原文与长度，便于排查截断位置
    logger.error('parse_llm_json 解析失败，原文长度=%s，原文：\n%s', len(text), text)
    raise ValueError(f"无法从 LLM 输出中提取 JSON（疑似被 max_tokens 截断），原文长度={len(text)}，前200字: {text[:200]}")


def safe_parse_llm_json(text: str, default: dict = None) -> dict:
    """安全版本：解析失败返回 default 而不是抛异常"""
    try:
        return parse_llm_json(text)
    except Exception:
        return default or {}
