import request from '@/utils/request'

/**
 * 个人中心-部门(班级)相关接口（仅需登录，不限数据范围）
 */

// 获取部门(班级)树，供个人中心选择班级
export function getProfileDeptTree() {
  return request({
    url: '/edu/profile/deptTree',
    method: 'get'
  })
}

// 学生：修改自己的班级（单值）
export function updateMyStudentClass(classId) {
  return request({
    url: '/edu/student/class',
    method: 'put',
    data: { classId }
  })
}

// 教师：获取自己已关联的班级列表
export function getMyTeacherClasses() {
  return request({
    url: '/edu/teacher/classes',
    method: 'get'
  })
}

// 教师：新增一个班级关联
export function addMyTeacherClass(classId) {
  return request({
    url: '/edu/teacher/class',
    method: 'post',
    data: { classId }
  })
}

// 教师：移除一个班级关联（按关联记录 id）
export function removeMyTeacherClass(tcId) {
  return request({
    url: `/edu/teacher/class/${tcId}`,
    method: 'delete'
  })
}
