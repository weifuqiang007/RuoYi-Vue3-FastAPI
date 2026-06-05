import request from '@/utils/request'

export function searchRetrieval(data) {
  return request({
    url: '/rag/retrieval/search',
    method: 'post',
    data: data
  })
}
