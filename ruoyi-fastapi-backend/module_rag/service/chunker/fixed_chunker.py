# module_rag/service/chunker/fixed_chunker.py
"""固定大小分块器  固定窗口 + 句子边界对齐 + overlap
核心思路来自 ragflow/rag/nlp/__init__.py 的 naive_merge() 函数（第1070-1126行）
1. 按 token 数累积分块
2. 超过 chunk_size 时在句子边界切分
3. 相邻 chunk 之间保留 overlap
"""

class FixedChunker:

    SENTENCE_ENDS = set("。！？；.!?;\n")

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict = None) -> list[dict]:
        """
        分块主函数
        参考 ragflow naive_merge() 的逻辑：
        - 累积 token 直到超过 chunk_size
        - 在句子边界处切分
        - 保留 overlap
        """
        if not text or not text.strip():
            return []

        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        overlap_text = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                # 当前 chunk 已满，保存
                if current_chunk:
                    chunks.append(self._make_chunk(current_chunk.strip(), metadata))
                    # overlap：取当前 chunk 尾部
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk

                # 如果段落本身超长，按句子边界切
                if len(para) > self.chunk_size:
                    sub_chunks = self._split_at_sentence(para, metadata, overlap_text)
                    chunks.extend(sub_chunks)
                    overlap_text = sub_chunks[-1]["content"][-self.overlap:] if sub_chunks else ""
                    current_chunk = ""
                else:
                    current_chunk = overlap_text + para + "\n\n"

        if current_chunk.strip():
            chunks.append(self._make_chunk(current_chunk.strip(), metadata))

        return chunks

    def _split_at_sentence(self, text: str, metadata: dict, prefix: str = "") -> list[dict]:
        """
        在句子边界处切分长文本
        参考 ragflow naive_merge 中的 overlap 逻辑
        """
        content = prefix + text
        chunks = []
        start = 0
        minimum_boundary = max(1, int(self.chunk_size * 0.6))

        while len(content) - start > self.chunk_size:
            hard_end = start + self.chunk_size
            boundary = -1
            for index in range(hard_end, start + minimum_boundary - 1, -1):
                if content[index - 1] in self.SENTENCE_ENDS:
                    boundary = index
                    break
            end = boundary if boundary > start else hard_end
            chunks.append(self._make_chunk(content[start:end].strip(), metadata))
            start = max(end - self.overlap, start + 1)

        remainder = content[start:].strip()
        if remainder:
            chunks.append(self._make_chunk(remainder, metadata))
        return chunks

    def _make_chunk(self, content: str, metadata: dict) -> dict:
        return {
            "content": content,
            "token_count": len(content),
            "metadata": dict(metadata or {}),
        }
