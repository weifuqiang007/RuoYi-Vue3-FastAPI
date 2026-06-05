<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>AI 提问引导</span>
        <div class="actions">
          <el-button type="primary" size="small" :loading="loading" :disabled="!reflectionId" @click="generate">
            请AI出新问题
          </el-button>
        </div>
      </div>
    </template>

    <div v-if="!reflectionId" class="empty">先保存反思内容后再生成提问</div>
    <div v-else-if="questions.length === 0" class="empty">暂无问题</div>
    <div v-else class="question-list">
      <div v-for="(q, idx) in questions" :key="idx" class="question-item">
        <el-tag size="small" type="primary">追问 {{ idx + 1 }}</el-tag>
        <div class="question-text">{{ formatQuestion(q) }}</div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import { generateReflectionQuestions } from '@/api/learning/reflection'

const props = defineProps({
  reflectionId: { type: [String, Number], default: null },
  initialQuestions: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:questions', 'update:theories', 'update:depth'])

const loading = ref(false)
const questions = ref([])

watch(
  () => props.initialQuestions,
  (v) => {
    questions.value = Array.isArray(v) ? v : []
  },
  { immediate: true }
)

function formatQuestion(q) {
  if (typeof q === 'string') return q
  if (q?.question) return q.question
  if (q?.content) return q.content
  return JSON.stringify(q)
}

async function generate() {
  if (!props.reflectionId) return
  loading.value = true
  try {
    const res = await generateReflectionQuestions({ reflection_id: props.reflectionId })
    const data = res.data || {}
    const nextQuestions = data.questions ?? data.question_list ?? data ?? []
    questions.value = Array.isArray(nextQuestions) ? nextQuestions : []
    emit('update:questions', questions.value)
    if (data.theories || data.linked_theories) {
      emit('update:theories', data.theories ?? data.linked_theories)
    }
    if (data.depth_score !== undefined || data.depth_level) {
      emit('update:depth', { depth_score: data.depth_score, depth_level: data.depth_level })
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.actions {
  display: flex;
  gap: 10px;
}
.empty {
  color: #909399;
  padding: 16px 0;
  text-align: center;
}
.question-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.question-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
}
.question-text {
  margin-top: 8px;
  white-space: pre-wrap;
  color: #606266;
  line-height: 1.6;
}
</style>

