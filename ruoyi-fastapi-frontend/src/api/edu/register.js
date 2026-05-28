import request from '@/utils/request'

// 获取可选角色列表
export function listEduRoles() {
  return request({
    url: '/edu/roles',
    headers: { isToken: false },
    method: 'get'
  })
}

// 学生注册
export function studentRegister(data) {
  return request({
    url: '/edu/register/student',
    headers: { isToken: false },
    method: 'post',
    data: data
  })
}

// 教师注册
export function teacherRegister(data) {
  return request({
    url: '/edu/register/teacher',
    headers: { isToken: false },
    method: 'post',
    data: data
  })
}
