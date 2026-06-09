import request from '@/utils/request'

export function startRecord(taskId) {
  return request({
    url: `/learning/record/start/${taskId}`,
    method: 'post'
  })
}

// 注意：自研课题创建已移至 task 层，使用 /learning/task/student/create 接口
// 详见 api/learning/task.js 中的 createStudentTopic 方法

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

