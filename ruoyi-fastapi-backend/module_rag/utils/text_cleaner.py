# module_rag/utils/text_cleaner.py
"""文本清洗工具
参考 ragflow/rag/nlp/__init__.py 的 find_codec() 和编码检测逻辑
"""

import re
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


def is_chinese(text: str) -> bool:
    """
    判断文本是否主要是中文
    直接抄自 ragflow/rag/nlp/__init__.py 的 is_chinese() 函数（第256-265行）
    """
    if not text:
        return False
    chinese = sum(1 for ch in text if '一' <= ch <= '鿿')
    return chinese / len(text) > 0.2