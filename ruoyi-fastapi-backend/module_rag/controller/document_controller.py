# module_rag/controller/document_controller.py
import io
from typing import Annotated, Optional
from urllib.parse import quote

from fastapi import File, Path, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import RoleInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_rag.entity.vo.document_vo import DocumentResponseModel
from module_rag.service.document_service import DocumentService
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
    """文档管理控制器 —— 仅做参数接收 + 调 service + 封装响应，业务逻辑全部下沉到 DocumentService"""

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
        docs = await DocumentService.get_doc_list(query_db, kb_id)
        return ResponseUtil.success(
            data=[DocumentResponseModel.model_validate(d).model_dump() for d in docs]
        )

    # ── 某个知识库下的文档列表（保留兼容）──────────
    @staticmethod
    @document_controller.get('/list/{kb_id}', summary='获取知识库下的文档列表')
    async def get_doc_list(
        kb_id: Annotated[int, Path(description='知识库ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        docs = await DocumentService.get_doc_list(query_db, kb_id)
        return ResponseUtil.success(
            data=[DocumentResponseModel.model_validate(d).model_dump() for d in docs]
        )

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
        解析/向量化失败时不回滚，保留记录并标记状态，接口仍返回成功（用户可重试）。
        """
        doc = await DocumentService.upload_document(query_db, kb_id, file, current_user.user.user_id)
        return ResponseUtil.success(data={
            'doc_id': doc.doc_id,
            'file_path': doc.file_path,
            'parse_status': doc.parse_status,
            'embed_status': doc.embed_status,
        })

    # ── 下载文档 ──────────────────────────────────
    @staticmethod
    @document_controller.get('/download/{doc_id}', summary='下载文档')
    async def download_document(
        doc_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        """从 MinIO 下载文档文件"""
        result = await DocumentService.get_file(query_db, doc_id)
        if result is None:
            return ResponseUtil.failure(msg='文档不存在或文件已损坏')
        doc, data = result
        # 文件名百分号编码：HTTP 头只能用 latin-1，中文必须先按 RFC 5987 做 URL 编码
        encoded_name = quote(doc.doc_name)
        return StreamingResponse(
            io.BytesIO(data),
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': (
                    f"attachment; filename={encoded_name}; filename*=UTF-8''{encoded_name}"
                )
            },
        )

    # ── 文档预览 ──────────────────────────────────
    @staticmethod
    @document_controller.get('/preview/{doc_id}', summary='获取文档预览URL')
    async def preview_document(
        doc_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        """获取 MinIO 预签名 URL，用于前端直接预览（PDF/图片等）"""
        result = await DocumentService.get_presigned_url(query_db, doc_id)
        if result is None:
            return ResponseUtil.failure(msg='文档不存在或获取预览地址失败')
        url, doc = result
        return ResponseUtil.success(data={'url': url, 'doc_name': doc.doc_name})

    # ── 删除文档 ──────────────────────────────────
    @staticmethod
    @document_controller.delete('/{doc_ids}', summary='删除文档')
    async def delete_document(
        doc_ids: Annotated[str, Path(description='文档ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        """删除文档（MinIO 文件 + 逻辑删除记录 + 知识库 doc_count-1）"""
        ids = [int(i) for i in doc_ids.split(',')]
        await DocumentService.delete_documents(query_db, ids)
        return ResponseUtil.success(msg='删除成功')
