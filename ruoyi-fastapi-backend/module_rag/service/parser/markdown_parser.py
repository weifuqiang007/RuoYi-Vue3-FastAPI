"""结构感知的 Markdown 解析器。"""

import re

from module_rag.utils.text_cleaner import find_codec


class MarkdownParser:
    """按标题层级和块类型解析 Markdown，并保留章节路径用于检索与溯源。"""

    _heading_re = re.compile(r'^(#{1,6})\s+(.+?)\s*$')
    _list_re = re.compile(r'^\s*(?:[-*+]|\d+[.)])\s+')
    _table_re = re.compile(r'^\s*\|.*\|\s*$')
    _reference_re = re.compile(r'^(?:参考文献|references|bibliography)\s*$', re.IGNORECASE)

    def parse(self, file_path: str) -> list[dict]:
        """解析 Markdown，返回带 heading_path、heading_level 和块类型的结构化块。"""
        with open(file_path, 'rb') as file:
            blob = file.read()

        text = blob.decode(find_codec(blob), errors='ignore')
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        blocks: list[dict] = []
        heading_stack: list[tuple[int, str]] = []
        buffer: list[str] = []
        buffer_type: str | None = None
        in_code_fence = False
        in_references = False

        def current_path() -> list[str]:
            return [title for _, title in heading_stack]

        def flush() -> None:
            nonlocal buffer, buffer_type
            content = '\n'.join(buffer).strip()
            if content:
                blocks.append({
                    'text': content,
                    'page': 0,
                    'type': 'reference' if in_references else (buffer_type or 'text'),
                    'heading_path': current_path(),
                })
            buffer = []
            buffer_type = None

        for line in text.split('\n'):
            stripped = line.strip()

            if stripped.startswith(('```', '~~~')):
                next_type = 'code'
                if buffer_type and buffer_type != next_type:
                    flush()
                buffer_type = next_type
                buffer.append(line)
                in_code_fence = not in_code_fence
                continue

            if not in_code_fence:
                heading_match = self._heading_re.match(line)
                if heading_match:
                    flush()
                    level = len(heading_match.group(1))
                    title = heading_match.group(2).strip().rstrip('#').strip()
                    while heading_stack and heading_stack[-1][0] >= level:
                        heading_stack.pop()
                    heading_stack.append((level, title))
                    in_references = any(
                        self._reference_re.match(path_title)
                        for _, path_title in heading_stack
                    )
                    blocks.append({
                        'text': title,
                        'page': 0,
                        'type': 'title',
                        'heading_path': current_path(),
                        'heading_level': level,
                    })
                    continue

            next_type = self._classify_line(line, in_code_fence)
            if not stripped:
                flush()
                continue
            if buffer_type and buffer_type != next_type:
                flush()
            buffer_type = next_type
            buffer.append(line)

        flush()
        return blocks

    @classmethod
    def _classify_line(cls, line: str, in_code_fence: bool) -> str:
        """识别检索需要区分的 Markdown 块类型。"""
        if in_code_fence:
            return 'code'
        if line.lstrip().startswith('>'):
            return 'quote'
        if cls._table_re.match(line):
            return 'table'
        if cls._list_re.match(line):
            return 'list'
        return 'text'
