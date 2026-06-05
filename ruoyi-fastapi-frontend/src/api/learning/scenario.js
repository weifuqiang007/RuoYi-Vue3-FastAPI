import request from '@/utils/request'

export function saveScenario(data) {
  return request({
    url: '/learning/scenario/save',
    method: data?.scenario_id ? 'put' : 'post',
    data: data
  })
}

export function analyzeScenario(data) {
  return request({
    url: '/learning/scenario/analyze',
    method: 'post',
    data: data
  })
}

export function confirmScenario(data) {
  return request({
    url: '/learning/scenario/confirm',
    method: 'put',
    data: data
  })
}

export function getScenarioDetail(recordId) {
  return request({
    url: `/learning/scenario/detail/${recordId}`,
    method: 'get'
  })
}

