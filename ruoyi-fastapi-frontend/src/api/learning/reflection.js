import request from '@/utils/request'

export function saveReflection(data) {
  return request({
    url: '/learning/reflection/save',
    method: data?.reflection_id ? 'put' : 'post',
    data: data
  })
}

export function generateReflectionQuestions(data) {
  return request({
    url: '/learning/reflection/questions',
    method: 'post',
    data: data
  })
}

export function getReflectionDepth(reflectionId) {
  return request({
    url: `/learning/reflection/depth/${reflectionId}`,
    method: 'get'
  })
}

export function getReflectionDepthHistory(reflectionId) {
  return request({
    url: `/learning/reflection/depth-history/${reflectionId}`,
    method: 'get'
  })
}

export function getReflectionDetail(recordId) {
  return request({
    url: `/learning/reflection/detail/${recordId}`,
    method: 'get'
  })
}

export function confirmReflection(data) {
  return request({
    url: '/learning/reflection/confirm',
    method: 'put',
    data: data
  })
}

