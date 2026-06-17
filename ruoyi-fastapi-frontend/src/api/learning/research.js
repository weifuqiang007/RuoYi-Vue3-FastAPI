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

// ── 非流式接口 ──

export function initResearch(recordId, force = false) {
  return request({
    url: `/learning/research/init/${recordId}`,
    method: 'post',
    data: { force }
  })
}

export function saveResearch(data) {
  return request({
    url: '/learning/research/save',
    method: 'put',
    data: data
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

// ── 流式接口 ──

export function generateResearchQuestionsStream(data, callbacks = {}, signal = null) {
  return streamFetch('/learning/research/questions/stream', data, callbacks, signal)
}

export function generateResearchFrameworkStream(data, callbacks = {}, signal = null) {
  return streamFetch('/learning/research/framework/stream', data, callbacks, signal)
}

export function draftResearchChapterStream(data, callbacks = {}, signal = null) {
  return streamFetch('/learning/research/chapter/draft/stream', data, callbacks, signal)
}

export function recommendResearchReferencesStream(data, callbacks = {}, signal = null) {
  return streamFetch('/learning/research/references/stream', data, callbacks, signal)
}
