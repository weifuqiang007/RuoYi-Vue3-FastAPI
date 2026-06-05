<template>
  <el-card shadow="never">
    <template #header>
      <div class="panel-header">
        <span>{{ title }}</span>
        <div class="panel-actions">
          <el-button size="small" @click="clear">清空</el-button>
        </div>
      </div>
    </template>

    <div class="chat-body">
      <div v-if="messages.length === 0" class="chat-empty">暂无对话</div>
      <div v-for="(m, idx) in messages" :key="idx" class="chat-line" :class="`role-${m.role}`">
        <div class="chat-role">{{ m.role === 'user' ? '我' : 'AI' }}</div>
        <div class="chat-content">{{ m.content }}</div>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="input"
        type="textarea"
        :rows="3"
        placeholder="输入内容..."
        @keydown.enter.exact.prevent="handleSend"
      />
      <div class="chat-buttons">
        <el-button type="primary" :loading="sending" :disabled="!input.trim()" @click="handleSend">发送</el-button>
        <el-button :disabled="!sending" @click="handleStop">停止</el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/auth'

const props = defineProps({
  title: {
    type: String,
    default: 'AI 对话'
  },
  requestUrl: {
    type: String,
    required: true
  },
  buildPayload: {
    type: Function,
    default: (text) => ({ message: text })
  }
})

const messages = ref([])
const input = ref('')
const sending = ref(false)
const abortController = ref(null)

function clear() {
  messages.value = []
}

async function handleSend() {
  const text = input.value.trim()
  if (!text) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  sending.value = true
  abortController.value = new AbortController()

  const aiIndex = messages.value.push({ role: 'assistant', content: '' }) - 1
  let buffer = ''
  const decoder = new TextDecoder()

  try {
    const response = await fetch(import.meta.env.VITE_APP_BASE_API + props.requestUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + getToken()
      },
      signal: abortController.value.signal,
      body: JSON.stringify(props.buildPayload(text))
    })

    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      const json = await response.json()
      const data = json?.data ?? json
      messages.value[aiIndex].content = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
      return
    }

    const reader = response.body?.getReader?.()
    if (!reader) {
      ElMessage.error('响应不支持流式读取')
      return
    }
    let aiContent = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) continue
        let piece = trimmed
        try {
          const parsed = JSON.parse(trimmed)
          piece = parsed?.content ?? parsed?.data ?? parsed?.text ?? trimmed
        } catch {
        }
        aiContent += String(piece)
        messages.value[aiIndex].content = aiContent
      }
    }
  } catch (err) {
    if (err?.name !== 'AbortError') {
      ElMessage.error('请求失败：' + (err?.message || '未知错误'))
    }
  } finally {
    sending.value = false
    abortController.value = null
  }
}

function handleStop() {
  abortController.value?.abort?.()
}
</script>

<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-body {
  min-height: 220px;
  max-height: 360px;
  overflow: auto;
}

.chat-empty {
  color: #909399;
  text-align: center;
  padding: 24px 0;
}

.chat-line {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f2f6fc;
}

.chat-role {
  width: 44px;
  flex-shrink: 0;
  color: #909399;
}

.chat-content {
  flex: 1;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-input {
  margin-top: 14px;
}

.chat-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}
</style>

