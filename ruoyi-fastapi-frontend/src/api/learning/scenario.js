import request from '@/utils/request'
import { getToken } from '@/utils/auth'

export function saveScenario(data) {
  return request({
    url: '/learning/scenario/save',
    method: data?.scenario_id ? 'put' : 'post',
    data: data
  })
}

export function analyzeScenario(data) {
  return request({
    url: '/learning/scenario/analyze',
    method: 'post',
    data: data
  })
}

/**
 * 流式 AI 分析 — 使用 fetch 绕过 axios 10s 全局超时
 * @param {Object} data - { scenario_id: number }
 * @param {Object} callbacks - { onStatus, onContent, onResult, onError }
 * @param {AbortSignal} [signal] - 可选的 AbortController.signal
 */
export function analyzeScenarioStream(data, callbacks = {}, signal = null) {
  const { onStatus, onContent, onResult, onError } = callbacks
  const baseUrl = import.meta.env.VITE_APP_BASE_API

  return fetch(baseUrl + '/learning/scenario/analyze/stream', {
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

    const reader = response.body.getReader()
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
        try {
          const parsed = JSON.parse(trimmed)
          if (parsed.type === 'status' && onStatus) {
            onStatus(parsed.message)
          } else if (parsed.type === 'content' && onContent) {
            onContent(parsed.content)
          } else if (parsed.type === 'result' && onResult) {
            onResult(parsed.data)
          } else if (parsed.type === 'error' && onError) {
            onError(parsed.message)
          }
        } catch {
          // 忽略非 JSON 行
        }
      }
    }
  })
}

export function confirmScenario(data) {
  return request({
    url: '/learning/scenario/confirm',
    method: 'put',
    data: data
  })
}

export function followupScenario(data) {
  return request({
    url: '/learning/scenario/followup',
    method: 'post',
    data: data
  })
}

export function getScenarioDetail(recordId) {
  return request({
    url: `/learning/scenario/detail/${recordId}`,
    method: 'get'
  })
}

