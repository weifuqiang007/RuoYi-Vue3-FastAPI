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

/** 获取学习记录下所有反思（按决策分 Tab） */
export function getReflectionList(recordId) {
  return request({
    url: `/learning/reflection/list/${recordId}`,
    method: 'get'
  })
}

/** 获取单个决策的反思详情 */
export function getReflectionByDecision(decisionId) {
  return request({
    url: `/learning/reflection/detail-by-decision/${decisionId}`,
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
