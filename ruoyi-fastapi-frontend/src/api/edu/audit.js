import request from '@/utils/request'

// ========== 审核管理（管理员/教师共用） ==========

// 查询用户列表
export function listManageUsers(query) {
  return request({
    url: '/edu/manage/users',
    method: 'get',
    params: query
  })
}

// 新增学生
export function addManageStudent(data) {
  return request({
    url: '/edu/manage/user/student',
    method: 'post',
    data: data
  })
}

// 新增教师
export function addManageTeacher(data) {
  return request({
    url: '/edu/manage/user/teacher',
    method: 'post',
    data: data
  })
}

// 编辑用户信息
export function updateManageUser(userId, data) {
  return request({
    url: `/edu/manage/user/${userId}`,
    method: 'put',
    data: data
  })
}

// 移除用户
export function deleteManageUser(userId) {
  return request({
    url: `/edu/manage/user/${userId}`,
    method: 'delete'
  })
}

// 审核用户（通过/拒绝）
export function auditManageUser(userId, data) {
  return request({
    url: `/edu/manage/audit/${userId}`,
    method: 'put',
    data: data
  })
}

// ========== 旧版审核接口（仅管理员，兼容保留） ==========

// 查询审核列表
export function listAudit(query) {
  return request({
    url: '/edu/audit/list',
    method: 'get',
    params: query
  })
}

// 审核通过
export function approveAudit(auditId, data) {
  return request({
    url: `/edu/audit/approve/${auditId}`,
    method: 'put',
    data: data
  })
}

// 审核拒绝
export function rejectAudit(auditId, data) {
  return request({
    url: `/edu/audit/reject/${auditId}`,
    method: 'put',
    data: data
  })
}
