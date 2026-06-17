import request from '@/utils/request'

// 教师批阅列表（按班级/任务/学生/状态筛选 + 分页）
export function listReviewRecords(query) {
  return request({
    url: '/learning/review/records',
    method: 'get',
    params: query
  })
}

// 批阅详情（四区 + 反思列表 + 批阅数据）
export function getReviewDetail(recordId) {
  return request({
    url: `/learning/review/detail/${recordId}`,
    method: 'get'
  })
}

// 生成 / 重新生成 AI 评论（裁判模型，约30-60秒，单独120秒超时）
export function generateAiComment(recordId, data) {
  return request({
    url: `/learning/review/ai-comment/${recordId}`,
    method: 'post',
    data: data || {},
    timeout: 120000
  })
}

// 老师提交 / 更新点评（评分 + 评语）
export function submitReviewComment(recordId, data) {
  return request({
    url: `/learning/review/comment/${recordId}`,
    method: 'put',
    data: data
  })
}

// AI 评论历史版本
export function listAiCommentHistory(recordId) {
  return request({
    url: `/learning/review/ai-comment-history/${recordId}`,
    method: 'get'
  })
}
