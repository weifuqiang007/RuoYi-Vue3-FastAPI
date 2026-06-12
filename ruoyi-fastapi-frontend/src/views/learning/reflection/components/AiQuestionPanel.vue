<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>AI 理论指导</span>
        <el-button
          type="primary"
          size="small"
          :loading="loading"
          :disabled="!reflectionId"
          @click="generate"
        >
          请AI生成理论指导
        </el-button>
      </div>
    </template>

    <div v-if="!reflectionId" class="empty">先保存反思内容后再生成理论指导</div>
    <div v-else-if="loading" class="empty">
      <el-icon class="is-loading"><Loading /></el-icon>
      AI 正在分析你的反思并匹配相关理论...
    </div>
    <div v-else-if="!hasContent" class="empty">暂无指导，点击上方按钮生成</div>
    <div v-else class="guidance-content">
      <!-- 理论指导 -->
      <div v-if="theoryGuidance.length" class="section">
        <div class="section-title">📖 关联理论</div>
        <div v-for="(g, idx) in theoryGuidance" :key="idx" class="theory-item">
          <div class="theory-name">
            {{ g.theory_name || g.name || '理论' }}
            <span v-if="g.theory_source" class="theory-source">（{{ g.theory_source }}）</span>
          </div>
          <div v-if="g.relevance" class="theory-relevance">
            <strong>关联：</strong>{{ g.relevance }}
          </div>
          <div v-if="g.suggestion" class="theory-suggestion">
            <strong>建议：</strong>{{ g.suggestion }}
          </div>
          <div v-if="g.description && !g.relevance && !g.suggestion" class="theory-desc">
            {{ g.description }}
          </div>
        </div>
      </div>

      <!-- 反思方向 -->
      <div v-if="reflectionDirection" class="section">
        <div class="section-title">💡 反思方向</div>
        <div class="direction-text">{{ reflectionDirection }}</div>
      </div>

      <!-- 追问 -->
      <div v-if="questions.length" class="section">
        <div class="section-title">📌 追问</div>
        <div v-for="(q, idx) in questions" :key="idx" class="question-item">
          <el-tag size="small" type="primary">追问 {{ idx + 1 }}</el-tag>
          <div class="question-text">{{ formatQuestion(q) }}</div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { generateReflectionQuestions } from '@/api/learning/reflection'

const props = defineProps({
  reflectionId: { type: [String, Number], default: null },
  initialGuidance: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['update:depth', 'update:guidance'])

const loading = ref(false)
const guidance = ref({})

watch(
  () => props.initialGuidance,
  (v) => { guidance.value = v || {} },
  { immediate: true }
)

const theoryGuidance = computed(() => {
  const g = guidance.value.theory_guidance || guidance.value.theories || []
  return Array.isArray(g) ? g : []
})

const reflectionDirection = computed(() => guidance.value.reflection_direction || '')

const questions = computed(() => {
  const q = guidance.value.questions || []
  return Array.isArray(q) ? q : []
})

const hasContent = computed(() =>
  theoryGuidance.value.length > 0 || reflectionDirection.value || questions.value.length > 0
)

function formatQuestion(q) {
  if (typeof q === 'string') return q
  return q?.question || q?.content || JSON.stringify(q)
}

async function generate() {
  if (!props.reflectionId) return
  loading.value = true
  try {
    const res = await generateReflectionQuestions({ reflection_id: props.reflectionId })
    const data = res.data || {}
    guidance.value = data
    emit('update:guidance', data)
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
.empty {
  color: #909399;
  padding: 16px 0;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.guidance-content .section {
  margin-bottom: 14px;
}
.guidance-content .section:last-child {
  margin-bottom: 0;
}
.section-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
  color: #303133;
}
.theory-item {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 8px;
}
.theory-item:last-child {
  margin-bottom: 0;
}
.theory-name {
  font-weight: 600;
  font-size: 14px;
  color: #409eff;
  margin-bottom: 6px;
}
.theory-source {
  color: #909399;
  font-weight: normal;
  font-size: 12px;
}
.theory-relevance, .theory-suggestion {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-top: 4px;
}
.theory-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
.direction-text {
  background: #ecf5ff;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
.question-item {
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px 12px;
}
.question-text {
  margin-top: 6px;
  white-space: pre-wrap;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}
</style>
