import request from '@/utils/request'

// 获取首页最近操作动态（登录后调用，自动带 token）
// limit 建议取 > 可视行数的值，前端可视区固定显示若干行、多余的无缝滚动轮播
export function getRecentActivities(limit = 20) {
  return request({
    url: '/learning/activity/recent',
    method: 'get',
    params: { limit }
  })
}

// 获取用户名片（动态墙人名点击时调用）
export function getUserCard(userId) {
  return request({
    url: '/learning/activity/user-card',
    method: 'get',
    params: { user_id: userId }
  })
}

// 校验当前用户对任务的数据权限，返回 { can_access, redirect_path, reason }
export function checkTaskAccess(taskId) {
  return request({
    url: '/learning/activity/check-task-access',
    method: 'get',
    params: { task_id: taskId }
  })
}
