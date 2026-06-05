import request from '@/utils/request'

export function initResearch(recordId) {
  return request({
    url: `/learning/research/init/${recordId}`,
    method: 'post'
  })
}

export function generateResearchQuestions(data) {
  return request({
    url: '/learning/research/questions',
    method: 'post',
    data: data
  })
}

export function generateResearchFramework(data) {
  return request({
    url: '/learning/research/framework',
    method: 'post',
    data: data
  })
}

export function saveResearchChapter(data) {
  return request({
    url: '/learning/research/chapter/save',
    method: 'put',
    data: data
  })
}

export function draftResearchChapter(data) {
  return request({
    url: '/learning/research/chapter/draft',
    method: 'post',
    data: data
  })
}

export function recommendResearchReferences(data) {
  return request({
    url: '/learning/research/references',
    method: 'post',
    data: data
  })
}

export function submitResearch(data) {
  return request({
    url: '/learning/research/submit',
    method: 'put',
    data: data
  })
}

