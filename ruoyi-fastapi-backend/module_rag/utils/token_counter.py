# module_rag/utils/token_counter.py
"""Token 计数工具
参考 ragflow/common/token_utils.py 的 num_tokens_from_string()
MVP 阶段用字符数近似，后续可接入 tiktoken
"""


def count_tokens(text: str) -> int:
    """
    估算 Token 数量
    中文约 1 字 ≈ 1.5 token，英文约 4 字符 ≈ 1 token
    MVP 阶段简化为字符数
    """
    if not text:
        return 0
    return len(text)


def truncate_text(text: str, max_tokens: int) -> str:
    """截断文本到最大 token 数"""
    if count_tokens(text) <= max_tokens:
        return text
    return text[:max_tokens]