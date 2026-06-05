import request from '@/utils/request'

export function listTeacherTask(query) {
  return request({
    url: '/learning/task/list',
    method: 'get',
    params: query
  })
}

export function createTask(data) {
  return request({
    url: '/learning/task/create',
    method: 'post',
    data: data
  })
}

export function updateTask(data) {
  return request({
    url: '/learning/task/update',
    method: 'put',
    data: data
  })
}

export function deleteTask(taskId) {
  return request({
    url: `/learning/task/delete/${taskId}`,
    method: 'delete'
  })
}

export function publishTask(taskId, data) {
  return request({
    url: `/learning/task/publish/${taskId}`,
    method: 'put',
    data: data
  })
}

export function listStudentTask(query) {
  return request({
    url: '/learning/task/student/list',
    method: 'get',
    params: query
  })
}

export function getTaskDetail(taskId) {
  return request({
    url: `/learning/task/detail/${taskId}`,
    method: 'get'
  })
}

