# module_rag/service/parser/docx_parser.py
"""DOCX 文档解析器
参考 ragflow/deepdoc/parser/docx_parser.py 的 RAGFlowDocxParser 类
提取段落文字和表格内容
"""
from docx import Document

class DocxParser:

    def parse(self, file_path: str) -> list[dict]:
        """
        解析DOCX文件
        返回：[{"text":"内容", "page":0, "type":"text/title/table"}]
        """
        doc = Document(file_path)
        blocks = []

        for element in doc.element.body:
            tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
            if tag == "p":
                #
                para_text = ''.join(node.text or '' for node in element.iter() if node.text)
                if not para_text.strip():
                    continue

                    # 判断是否标题（参考 ragflow 的 docx_question_level 函数）
                para_style = ''
                for p in doc.paragraphs:
                    if p._element is element:
                        para_style = p.style.name if p.style else ''
                        break

                block_type = 'title' if 'Heading' in para_style or 'heading' in para_style else 'text'
                blocks.append({
                    "text": para_text.strip(),
                    "page": 0,
                    "type": block_type,
                })

            elif tag == 'tbl':
                # 表格处理 — 参考 ragflow 的 __extract_table_content 方法
                table_text = self._extract_table(element, doc)
                if table_text.strip():
                    blocks.append({
                        "text": table_text,
                        "page": 0,
                        "type": "table",
                    })

            return blocks

    def _extract_table(self, tbl_element, doc) -> str:
        """提取表格文本 — 参考 ragflow 的 __extract_table_content"""
        for table in doc.tables:
            if table._element is tbl_element:
                rows = []
                for row in table.rows:
                    rows.append(' | '.join(cell.text.strip() for cell in row.cells))
                return '\n'.join(rows)
        return ""
