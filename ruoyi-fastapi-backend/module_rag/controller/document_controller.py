# module_rag/controller/document_controller.py
import os
from typing import Annotated
from fastapi import File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from config.env import UploadConfig
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_rag.dao.document_dao import DocumentDao
from module_rag.entity.do.document_do import RagDocument
from module_rag.service.document_service import DocumentService
from utils.response_util import ResponseUtil

document_controller = APIRouterPro(
    prefix='/rag/document', order_num=21, tags=['RAG管理-文档'], dependencies=[PreAuthDependency()]
)


@document_controller.post('/upload/{kb_id}', summary='上传文档到知识库')
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: CurrentUserModel = CurrentUserDependency(),
):
    # 保存文件
    upload_dir = os.path.join(UploadConfig.UPLOAD_PATH, 'rag')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    # 获取文件类型
    file_type = os.path.splitext(file.filename)[1].lower()

    # 创建文档记录
    doc = RagDocument(
        kb_id=kb_id,
        doc_name=file.filename,
        file_path=file_path,
        file_type=file_type,
        file_size=len(content),
        user_id=current_user.user.user_id,
    )
    doc = await DocumentDao.create(query_db, doc)

    # 触发异步处理（MVP 阶段同步执行）
    await DocumentService.process_document(query_db, doc.doc_id)
    await query_db.commit()

    return ResponseUtil.success(data={"doc_id": doc.doc_id})


@document_controller.get('/list/{kb_id}', summary='获取知识库下的文档列表')
async def get_doc_list(
    kb_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
):
    docs = await DocumentDao.get_by_kb_id(query_db, kb_id)
    return ResponseUtil.success(data=[{
        "doc_id": d.doc_id,
        "doc_name": d.doc_name,
        "file_type": d.file_type,
        "parse_status": d.parse_status,
        "embed_status": d.embed_status,
        "chunk_count": d.chunk_count,
    } for d in docs])