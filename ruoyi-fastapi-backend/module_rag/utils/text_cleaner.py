# module_rag/utils/text_cleaner.py
"""文本清洗工具
参考 ragflow/rag/nlp/__init__.py 的 find_codec() 和编码检测逻辑
"""

import re
import hashlib
import chardet


def find_codec(blob: bytes)-> str:
    """
    检测二进制数据的编码格式
    直接抄自 ragflow/rag/nlp/__init__.py 的 find_codec() 函数（第54-72行）
    """
    detected = chardet.detect(blob[:1024])
    if detected['confidence'] > 0.5:
        if detected['encoding'] == "ascii":
            return "utf-8"
        return detected['encoding']

    common_codecs = [
        'utf-8', 'gb2312', 'gbk', 'utf_16', 'ascii', 'big5',
        'gb18030', 'latin_1', 'utf_16_be', 'utf_16_le',
    ]

    for c in common_codecs:
        try:
            blob[:1024].decode(c)
            return c
        except Exception:
            pass
    return "utf-8"


def clean_text(text: str) -> str:
    """清洗文本：去除多余空白、特殊字符"""
    # 去除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空白
    return text.strip()


def clean_block_text(text: str) -> str:
    """清洗解析后的文本，同时保留段落、列表和表格所需的换行结构。"""
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\u00a0', ' ').replace('\u200b', '')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def is_valid_chunk(content: str, min_length: int = 20) -> bool:
    """过滤空白、过短和明显由不可打印字符构成的分块。"""
    normalized = re.sub(r'\s+', '', content or '')
    if len(normalized) < min_length:
        return False
    printable = sum(1 for char in normalized if char.isprintable())
    return printable / len(normalized) >= 0.9


def content_fingerprint(content: str) -> str:
    """生成忽略空白和大小写的稳定指纹，用于文档内精确去重。"""
    normalized = re.sub(r'\s+', '', content or '').casefold()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def is_chinese(text: str) -> bool:
    """
    判断文本是否主要是中文
    直接抄自 ragflow/rag/nlp/__init__.py 的 is_chinese() 函数（第256-265行）
    """
    if not text:
        return False
    chinese = sum(1 for ch in text if '一' <= ch <= '鿿')
    return chinese / len(text) > 0.2
