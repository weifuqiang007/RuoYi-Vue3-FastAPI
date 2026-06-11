import request from '@/utils/request'

export function saveDecision(data) {
  return request({
    url: '/learning/decision/save',
    method: data?.decision_id ? 'put' : 'post',
    data: data
  })
}

export function ethicsAnalyzeDecision(data) {
  return request({
    url: '/learning/decision/ethics-analyze',
    method: 'post',
    data: data
  })
}

export function generateDecisionAlternatives(data) {
  return request({
    url: '/learning/decision/alternatives',
    method: 'post',
    data: data
  })
}

export function listDecision(recordId) {
  return request({
    url: `/learning/decision/list/${recordId}`,
    method: 'get'
  })
}

export function deleteDecision(decisionId) {
  return request({
    url: `/learning/decision/${decisionId}`,
    method: 'delete'
  })
}

export function confirmDecision(recordId) {
  return request({
    url: `/learning/decision/confirm/${recordId}`,
    method: 'put'
  })
}
