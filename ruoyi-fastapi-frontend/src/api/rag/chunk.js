import request from '@/utils/request'

// 分页获取某文档的分块列表
export function listChunk(docId, pageNum = 1, pageSize = 20) {
  return request({
    url: `/rag/chunk/list/${docId}`,
    method: 'get',
    params: { page_num: pageNum, page_size: pageSize }
  })
}

// 修改分块内容（后端会自动重新向量化）
export function updateChunk(data) {
  return request({
    url: '/rag/chunk',
    method: 'put',
    data
  })
}
