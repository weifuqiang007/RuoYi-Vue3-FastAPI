# module_rag/service/parser/txt_parser.py
"""TXT/MD 文件解析器"""
from module_rag.utils.text_cleaner import find_codec


class TxtParser:

    def parse(self, file_path: str) -> list[dict]:
        """解析 TXT/MD 文件"""
        with open(file_path, 'rb') as f:
            blob = f.read()

        codec = find_codec(blob)
        text = blob.decode(codec, errors='ignore')

        # 按空行分段
        paragraphs = text.split('\n\n')
        blocks = []
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            # Markdown 标题识别
            block_type = 'title' if para.startswith('#') else 'text'
            blocks.append({
                "text": para,
                "page": 0,
                "type": block_type,
            })

        return blocks