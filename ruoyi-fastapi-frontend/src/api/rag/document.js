import request from '@/utils/request'

export function listAllDocument(kbId) {
  const hasKbId = kbId !== null && kbId !== undefined && kbId !== ''
  return request({
    url: '/rag/document/list',
    method: 'get',
    params: hasKbId ? { kb_id: kbId } : {}
  })
}

export function listDocument(kbId) {
  return request({
    url: `/rag/document/list/${kbId}`,
    method: 'get'
  })
}

export function uploadDocument(kbId, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: `/rag/document/upload/${kbId}`,
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function downloadDocument(docId) {
  return request({
    url: `/rag/document/download/${docId}`,
    method: 'get',
    responseType: 'blob'
  })
}

export function previewDocument(docId) {
  return request({
    url: `/rag/document/preview/${docId}`,
    method: 'get'
  })
}

export function delDocument(docIds) {
  return request({
    url: `/rag/document/${docIds}`,
    method: 'delete'
  })
}
