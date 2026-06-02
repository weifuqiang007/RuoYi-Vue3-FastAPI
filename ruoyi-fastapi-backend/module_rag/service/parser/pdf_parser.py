# module_rag/service/parser/pdf_parser.py
"""PDF 文档解析器
参考 ragflow/deepdoc/parser/pdf_parser.py 的段落识别逻辑
简化版：去掉视觉模型，保留文本结构识别
"""
import fitz  # PyMuPDF


class PdfParser:
    """
    PDF 解析器
    核心思路参考 ragflow/deepdoc/parser/pdf_parser.py：
    1. 按字体大小判断标题 vs 正文
    2. 跨页段落合并
    """

    def parse(self, file_path: str) -> list[dict]:
        """
        解析 PDF 文件
        返回: [{"text": "段落内容", "page": 1, "type": "text/title"}, ...]
        """
        doc = fitz.open(file_path)
        blocks = []

        for page_num, page in enumerate(doc):
            text_dict = page.get_text("dict")
            for block in text_dict["blocks"]:
                if block["type"] != 0:  # 只处理文字块
                    continue
                block_text = self._extract_block_text(block)
                if not block_text.strip():
                    continue
                block_type = self._classify_block(block)
                blocks.append({
                    "text": block_text,
                    "page": page_num + 1,
                    "type": block_type,
                })

        doc.close()
        return self._merge_paragraphs(blocks)

    def _extract_block_text(self, block: dict) -> str:
        """提取 block 中的所有文字"""
        lines_text = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                lines_text.append(span.get("text", ""))
        return "".join(lines_text)

    def _classify_block(self, block: dict) -> str:
        """
        参考 ragflow/deepdoc/parser/pdf_parser.py 的标题识别：
        字体大小 > 阈值 → title；否则 → text
        """
        font_sizes = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if span.get("text", "").strip():
                    font_sizes.append(span.get("size", 12))

        if not font_sizes:
            return "text"

        max_font_size = max(font_sizes)
        # RAGFlow 的判断逻辑：大于正文字体的认为是标题
        return "title" if max_font_size > 14 else "text"

    def _merge_paragraphs(self, blocks: list[dict]) -> list[dict]:
        """
        关键：把被切碎的段落合并回来
        参考 ragflow/rag/nlp/__init__.py 的 naive_merge() 函数逻辑（第1070-1126行）
        核心判断：上一个 block 没有以句号等结尾，且下一个 block 不是标题 → 合并
        """
        if not blocks:
            return []

        merged = [dict(blocks[0])]
        for block in blocks[1:]:
            last = merged[-1]
            should_merge = (
                last["type"] == "text"
                and block["type"] == "text"
                and not last["text"].rstrip().endswith(("。", "！", "？", ".", "!", "?", "；", ";"))
            )
            if should_merge:
                merged[-1]["text"] += block["text"]
            else:
                merged.append(dict(block))

        return merged