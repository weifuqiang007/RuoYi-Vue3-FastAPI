"""批量重新向量化所有文档。

用途：更换 embedding 模型/提供方后，存量分块的向量属于旧向量空间，必须重新生成。

执行方式（在 backend 目录、使用项目 Python 环境）：
    python scripts/reembed_all_documents.py

说明：
- 复用 DocumentService.process_document，该流程会先清理旧分块再重新解析/分块/向量化，幂等可重跑。
- 逐文档提交；单文档失败只影响自身（记录错误并置 embed_status=9），不中断整体。
"""

import asyncio

from sqlalchemy import select

from config.database import AsyncSessionLocal, async_engine
from module_rag.entity.do.document_do import RagDocument
from module_rag.service.document_service import DocumentService
from utils.log_util import logger


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(RagDocument)
            .where(RagDocument.del_flag == '0')
            .order_by(RagDocument.doc_id)
        )
        docs = list(result.scalars().all())
        print(f'共 {len(docs)} 个文档待重新向量化')

        for index, doc in enumerate(docs, start=1):
            print(f'[{index}/{len(docs)}] 处理文档 {doc.doc_id}: {doc.doc_name}')
            try:
                await DocumentService.process_document(db, doc.doc_id)
                await db.commit()
                print(f'  文档 {doc.doc_id} 处理完成')
            except Exception:
                logger.exception(f'文档 {doc.doc_id} 重新向量化失败')
                await db.rollback()

    await async_engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
