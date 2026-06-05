# module_rag/controller/document_controller.py
import os
import uuid
from typing import Annotated, Optional

from fastapi import File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import RoleInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_rag.dao.document_dao import DocumentDao
from module_rag.entity.do.document_do import RagDocument
from module_rag.service.document_service import DocumentService
from module_rag.utils.minio_client import MinioClient
from utils.response_util import ResponseUtil

# ──────────────────────────────────────────────
# 路由定义
# 角色校验通过路由级依赖实现 AOP 效果，
# 所有注册在该路由下的接口自动生效，无需手动调用 check_role
# ──────────────────────────────────────────────
document_controller = APIRouterPro(
    prefix='/rag/document',
    order_num=21,
    tags=['RAG管理-文档'],
    dependencies=[
        PreAuthDependency(),
        RoleInterfaceAuthDependency(['admin', 'teacher']),
    ],
)


class DocumentController:
    """文档管理控制器 —— 支持独立页面模式（全部文档 + 按知识库筛选）"""

    # ── 全部文档列表（新增，支持可选 kb_id 筛选）──────────
    # 注意：此路由必须注册在 /list/{kb_id} 之前，
    # 否则 FastAPI 会将 "list" 当作 kb_id 参数匹配到路径参数路由
    @staticmethod
    @document_controller.get('/list', summary='获取全部文档列表')
    async def get_all_doc_list(
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        kb_id: Optional[int] = Query(None, description='按知识库ID筛选，不传则返回全部'),
    ):
        """
        获取全部文档列表，支持按知识库筛选。
        - 不传 kb_id：返回所有文档
        - 传 kb_id：返回指定知识库下的文档
        """
        if kb_id is not None:
            docs = await DocumentDao.get_by_kb_id(query_db, kb_id)
        else:
            docs = await DocumentDao.get_all(query_db)
        return ResponseUtil.success(data=[{
            "doc_id": d.doc_id,
            "kb_id": d.kb_id,
            "doc_name": d.doc_name,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "parse_status": d.parse_status,
            "embed_status": d.embed_status,
            "chunk_count": d.chunk_count,
            "create_time": str(d.create_time) if d.create_time else None,
        } for d in docs])

    # ── 某个知识库下的文档列表（保留兼容）──────────
    @staticmethod
    @document_controller.get('/list/{kb_id}', summary='获取知识库下的文档列表')
    async def get_doc_list(
        kb_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        docs = await DocumentDao.get_by_kb_id(query_db, kb_id)
        return ResponseUtil.success(data=[{
            "doc_id": d.doc_id,
            "kb_id": d.kb_id,
            "doc_name": d.doc_name,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "parse_status": d.parse_status,
            "embed_status": d.embed_status,
            "chunk_count": d.chunk_count,
            "create_time": str(d.create_time) if d.create_time else None,
        } for d in docs])

    # ── 上传文档到知识库 ──────────────────────────
    @staticmethod
    @document_controller.post('/upload/{kb_id}', summary='上传文档到知识库')
    async def upload_document(
        kb_id: int,
        file: UploadFile = File(...),
        query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
        current_user: CurrentUserModel = CurrentUserDependency(),
    ):
        """
        上传文档 → 保存到 MinIO → 创建数据库记录 → 触发解析Pipeline
        """
        content = await file.read()
        file_type = os.path.splitext(file.filename)[1].lower()

        # 上传到 MinIO
        # 对象路径: rag/{kb_id}/{uuid}.{ext}
        object_name = f"rag/{kb_id}/{uuid.uuid4().hex}{file_type}"
        minio = MinioClient.get_instance()
        minio.put(object_name, content)

        # 创建文档记录（file_path 存的是 MinIO 的 object_name）
        doc = RagDocument(
            kb_id=kb_id,
            doc_name=file.filename,
            file_path=object_name,
            file_type=file_type,
            file_size=len(content),
            user_id=current_user.user.user_id,
        )
        doc = await DocumentDao.create(query_db, doc)

        # 触发异步处理（MVP 阶段同步执行）
        await DocumentService.process_document(query_db, doc.doc_id)

        return ResponseUtil.success(data={"doc_id": doc.doc_id, "file_path": object_name})

    # ── 下载文档 ──────────────────────────────────
    @staticmethod
    @document_controller.get('/download/{doc_id}', summary='下载文档')
    async def download_document(
        doc_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        """从 MinIO 下载文档文件"""
        doc = await DocumentDao.get_by_id(query_db, doc_id)
        if not doc:
            return ResponseUtil.failure(msg="文档不存在")

        minio = MinioClient.get_instance()
        data = minio.get(doc.file_path)
        if data is None:
            return ResponseUtil.failure(msg="文件不存在或已损坏")

        import io
        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{doc.doc_name}"},
        )

    # ── 文档预览 ──────────────────────────────────
    @staticmethod
    @document_controller.get('/preview/{doc_id}', summary='获取文档预览URL')
    async def preview_document(
        doc_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        """获取 MinIO 预签名 URL，用于前端直接预览（PDF/图片等）"""
        doc = await DocumentDao.get_by_id(query_db, doc_id)
        if not doc:
            return ResponseUtil.failure(msg="文档不存在")

        minio = MinioClient.get_instance()
        url = minio.get_presigned_url(doc.file_path)
        if url is None:
            return ResponseUtil.failure(msg="获取预览地址失败")

        return ResponseUtil.success(data={"url": url, "doc_name": doc.doc_name})

    # ── 删除文档 ──────────────────────────────────
    @staticmethod
    @document_controller.delete('/{doc_ids}', summary='删除文档')
    async def delete_document(
        doc_ids: str,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        """删除文档（MinIO 文件 + 数据库记录）"""
        ids = [int(i) for i in doc_ids.split(',')]
        minio = MinioClient.get_instance()

        for doc_id in ids:
            doc = await DocumentDao.get_by_id(query_db, doc_id)
            if doc:
                # 删除 MinIO 文件
                minio.remove(doc.file_path)
                # 逻辑删除数据库记录
                await DocumentDao.update_status(query_db, doc_id, del_flag='2')

        return ResponseUtil.success(msg="删除成功")
