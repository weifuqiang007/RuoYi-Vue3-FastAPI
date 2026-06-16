import request from '@/utils/request'
import { getToken } from '@/utils/auth'

/**
 * 通用流式请求封装 — 使用 fetch 绕过 axios 超时
 */
function streamFetch(url, data, callbacks = {}, signal = null) {
  const { onStatus, onContent, onResult, onError } = callbacks
  const baseUrl = import.meta.env.VITE_APP_BASE_API

  return fetch(baseUrl + url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + getToken()
    },
    signal,
    body: JSON.stringify(data)
  }).then(async (response) => {
    if (!response.ok) {
      const text = await response.text()
      throw new Error(`HTTP ${response.status}: ${text}`)
    }

    const reader = response.body?.getReader?.()
    if (!reader) {
      throw new Error('当前浏览器不支持流式读取')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) continue
        let parsed
        try {
          parsed = JSON.parse(trimmed)
        } catch {
          continue
        }
        if (parsed.type === 'status') {
          onStatus?.(parsed.message)
        } else if (parsed.type === 'content') {
          onContent?.(parsed.content)
        } else if (parsed.type === 'result') {
          onResult?.(parsed.data)
        } else if (parsed.type === 'error') {
          const message = parsed.message || parsed.error || '生成失败'
          onError?.(message)
          throw new Error(message)
        }
      }
    }
  })
}

export function saveReflection(data) {
  return request({
    url: '/learning/reflection/save',
    method: data?.reflection_id ? 'put' : 'post',
    data: data
  })
}

export function generateReflectionQuestions(data) {
  return request({
    url: '/learning/reflection/questions',
    method: 'post',
    data: data
  })
}

/** 流式生成理论指导（逐字回显） */
export function generateReflectionQuestionsStream(data, callbacks = {}, signal = null) {
  return streamFetch('/learning/reflection/questions/stream', data, callbacks, signal)
}

export function getReflectionDepth(reflectionId) {
  return request({
    url: `/learning/reflection/depth/${reflectionId}`,
    method: 'get'
  })
}

export function getReflectionDepthHistory(reflectionId) {
  return request({
    url: `/learning/reflection/depth-history/${reflectionId}`,
    method: 'get'
  })
}

/** 获取学习记录下所有反思（按决策分 Tab） */
export function getReflectionList(recordId) {
  return request({
    url: `/learning/reflection/list/${recordId}`,
    method: 'get'
  })
}

/** 获取单个决策的反思详情 */
export function getReflectionByDecision(decisionId) {
  return request({
    url: `/learning/reflection/detail-by-decision/${decisionId}`,
    method: 'get'
  })
}

export function confirmReflection(data) {
  return request({
    url: '/learning/reflection/confirm',
    method: 'put',
    data: data
  })
}
