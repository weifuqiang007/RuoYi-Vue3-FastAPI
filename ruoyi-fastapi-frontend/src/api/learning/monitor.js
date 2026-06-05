import request from '@/utils/request'

export function getClassOverview(taskId) {
  return request({
    url: `/learning/monitor/class/${taskId}`,
    method: 'get'
  })
}

export function getStudentDetail(recordId) {
  return request({
    url: `/learning/monitor/student/${recordId}`,
    method: 'get'
  })
}

export function submitEvaluation(data) {
  return request({
    url: '/learning/evaluation/submit',
    method: 'post',
    data: data
  })
}

export function getEvaluationDetail(recordId) {
  return request({
    url: `/learning/evaluation/detail/${recordId}`,
    method: 'get'
  })
}

export function markExcellent(recordId) {
  return request({
    url: `/learning/evaluation/mark-excellent/${recordId}`,
    method: 'put'
  })
}

export function listCases() {
  return request({
    url: '/learning/case/list',
    method: 'get'
  })
}

export function getCaseDetail(caseId) {
  return request({
    url: `/learning/case/detail/${caseId}`,
    method: 'get'
  })
}
