import request from '@/utils/request'

export function startRecord(taskId) {
  return request({
    url: `/learning/record/start/${taskId}`,
    method: 'post'
  })
}

export function createSelfRecord(data) {
  return request({
    url: '/learning/record/create-self',
    method: 'post',
    data: data
  })
}

export function listMyRecord(query) {
  return request({
    url: '/learning/record/my',
    method: 'get',
    params: query
  })
}

export function getRecordDetail(recordId) {
  return request({
    url: `/learning/record/detail/${recordId}`,
    method: 'get'
  })
}

export function advanceRecordStage(recordId) {
  return request({
    url: `/learning/record/advance/${recordId}`,
    method: 'put'
  })
}

