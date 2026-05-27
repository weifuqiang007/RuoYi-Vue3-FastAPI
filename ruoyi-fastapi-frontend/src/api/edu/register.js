import request from '@/utils/request'

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
