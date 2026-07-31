# module_rag/service/parser/__init__.py
from module_rag.service.parser.pdf_parser import PdfParser
from module_rag.service.parser.docx_parser import DocxParser
from module_rag.service.parser.markdown_parser import MarkdownParser
from module_rag.service.parser.txt_parser import TxtParser

# 文件类型 -- 》 解析器映射
PARSER_MAP = {
    '.pdf': PdfParser,
    '.docx': DocxParser,
    '.doc': DocxParser,
    '.txt': TxtParser,
    '.md': MarkdownParser,
}

def get_parser(file_type: str):
    """根据文件类型获取对应的解析器"""
    parser_cls = PARSER_MAP.get(file_type.lower())
    if not parser_cls:
        raise ValueError(f"不支持的文件类型: {file_type}")
    return parser_cls()
