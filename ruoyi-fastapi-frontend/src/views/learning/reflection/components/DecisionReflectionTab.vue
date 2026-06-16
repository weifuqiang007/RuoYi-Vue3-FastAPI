<template>
  <div class="decision-reflection-tab">
    <!-- 反思编辑器 -->
    <el-input
      v-model="content"
      type="textarea"
      :rows="8"
      placeholder="针对这个关键事件进行反身性反思：发生了什么？为什么？你在其中的立场、价值与关系是什么？"
      class="mb12"
    />

    <!-- 操作按钮 -->
    <div class="tab-actions mb12">
      <el-button :loading="saving" size="small" @click="save">
        <el-icon><Check /></el-icon> 保存反思
      </el-button>
      <el-button
        type="primary"
        size="small"
        :loading="generating"
        :disabled="!reflectionId"
        @click="generateGuidance"
      >
        <el-icon><MagicStick /></el-icon> 生成理论指导
      </el-button>
    </div>

    <!-- 流式生成逐字预览 -->
    <div v-if="generating || streamText" class="stream-preview">
      <div class="section-title">📖 AI 正在生成理论指导...</div>
      <div class="stream-text">{{ displayStreamText }}<span class="cursor">▋</span></div>
    </div>

    <!-- AI 理论指导展示 -->
    <div v-if="latestGuidance && hasGuidanceContent(latestGuidance)" class="inline-guidance">
      <el-divider content-position="left">AI 理论指导</el-divider>

      <div v-if="getGuidanceTheories(latestGuidance).length" class="section">
        <div class="section-title">📖 关联理论</div>
        <div v-for="(g, idx) in getGuidanceTheories(latestGuidance)" :key="idx" class="theory-item">
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
        </div>
      </div>

      <div v-if="latestGuidance.reflection_direction" class="section">
        <div class="section-title">💡 反思方向</div>
        <div class="direction-text">{{ latestGuidance.reflection_direction }}</div>
      </div>

      <div v-if="getGuidanceQuestions(latestGuidance).length" class="section">
        <div class="section-title">📌 追问</div>
        <div v-for="(q, idx) in getGuidanceQuestions(latestGuidance)" :key="idx" class="question-item">
          <el-tag size="small" type="primary">追问 {{ idx + 1 }}</el-tag>
          <div class="question-text">{{ formatQuestion(q) }}</div>
        </div>
      </div>
    </div>

    <!-- 历史轮次（只读） -->
    <ReflectionRoundCard
      v-for="(round, idx) in historyRounds"
      :key="'round-' + idx"
      :round-index="idx"
      :is-current="false"
      :dialogue-content="round.content"
      :depth-score-after="round.depthScoreAfter"
      :depth-score-before="round.depthScoreBefore"
      :time="round.createTime"
      class="mb8"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, MagicStick } from '@element-plus/icons-vue'
import { saveReflection, generateReflectionQuestions, generateReflectionQuestionsStream, getReflectionDepthHistory } from '@/api/learning/reflection'
import ReflectionRoundCard from './ReflectionRoundCard.vue'

const props = defineProps({
  decisionId: { type: [Number, String], required: true },
  keyEventDesc: { type: String, default: '' },
  recordId: { type: [Number, String], required: true },
  reflectionData: { type: Object, default: () => null }
})

const emit = defineEmits(['saved', 'guidance-generated', 'depth-loaded'])

const reflectionId = ref(null)
const content = ref('')
const latestGuidance = ref(null)
const dialogues = ref([])
const depthHistory = ref([])
const streamText = ref('')   // 流式逐字预览文本

const saving = ref(false)
const generating = ref(false)

/** 历史轮次 = 所有 assistant 对话 */
const historyRounds = computed(() => {
  return dialogues.value
    .filter(d => d.role === 'assistant')
    .map((d, idx) => ({
      content: d.content,
      depthScoreAfter: d.depth_score_after ?? d.depthScoreAfter ?? null,
      depthScoreBefore: d.depth_score_before ?? d.depthScoreBefore ?? null,
      createTime: d.create_time ?? d.createTime ?? '',
      index: idx,
    }))
})

/** 流式预览：剥离结尾的 ```json 结构化块，只展示可读 Markdown 部分 */
const displayStreamText = computed(() => {
  const text = streamText.value || ''
  const idx = text.indexOf('```json')
  return idx >= 0 ? text.slice(0, idx).trim() : text.trim()
})

// 初始化：从父组件传入的 reflectionData 加载
watch(() => props.reflectionData, (data) => {
  if (data) {
    reflectionId.value = data.reflection_id ?? data.reflectionId ?? null
    content.value = data.content ?? ''
    dialogues.value = normalizeArray(data.dialogues ?? [])
    // 从最后一条 assistant 对话恢复 latestGuidance
    const assistantDialogues = dialogues.value.filter(d => d.role === 'assistant')
    if (assistantDialogues.length > 0) {
      const last = assistantDialogues[assistantDialogues.length - 1]
      try {
        latestGuidance.value = typeof last.content === 'string'
          ? JSON.parse(last.content)
          : last.content
      } catch {
        latestGuidance.value = null
      }
    }
    loadDepthHistory()
  }
}, { immediate: true })

function normalizeArray(v) {
  if (!v) return []
  if (Array.isArray(v)) return v
  return [v]
}

function getGuidanceTheories(data) {
  if (!data) return []
  const g = data.theory_guidance || data.theories || []
  return Array.isArray(g) ? g : []
}

function getGuidanceQuestions(data) {
  if (!data) return []
  const q = data.questions || []
  return Array.isArray(q) ? q : []
}

function hasGuidanceContent(data) {
  if (!data) return false
  return getGuidanceTheories(data).length > 0
    || !!data.reflection_direction
    || getGuidanceQuestions(data).length > 0
}

function formatQuestion(q) {
  if (typeof q === 'string') return q
  return q?.question || q?.content || JSON.stringify(q)
}

async function loadDepthHistory() {
  if (!reflectionId.value) {
    depthHistory.value = []
    emit('depth-loaded', { decisionId: props.decisionId, depthHistory: [] })
    return
  }
  const res = await getReflectionDepthHistory(reflectionId.value)
  depthHistory.value = Array.isArray(res.data) ? res.data : []
  emit('depth-loaded', { decisionId: props.decisionId, depthHistory: depthHistory.value })
}

async function save() {
  if (!content.value.trim()) {
    ElMessage.warning('请先填写反思内容')
    return
  }
  saving.value = true
  try {
    const res = await saveReflection({
      decision_id: props.decisionId,
      reflection_id: reflectionId.value,
      content: content.value
    })
    const data = res.data || {}
    if (!reflectionId.value) {
      reflectionId.value = data.reflection_id ?? data.reflectionId ?? null
    }
    await loadDepthHistory()
    emit('saved', {
      decisionId: props.decisionId,
      reflectionId: reflectionId.value,
      depthScore: Number(data.depth_score ?? 0),
      depthLevel: data.depth_level ?? '',
    })
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}

async function generateGuidance() {
  if (!reflectionId.value) {
    ElMessage.warning('请先保存反思内容')
    return
  }
  generating.value = true
  streamText.value = ''
  latestGuidance.value = null
  try {
    await generateReflectionQuestionsStream(
      { reflection_id: reflectionId.value },
      {
        onStatus: () => {},
        onContent: (chunk) => {
          // 逐字追加，剥离结尾的 ```json 结构化块，只展示可读部分
          streamText.value += chunk
        },
        onResult: async (data) => {
          latestGuidance.value = data
          streamText.value = ''
          // 刷新深度历史并上报父组件
          await loadDepthHistory()
          emit('guidance-generated', {
            decisionId: props.decisionId,
            depthScore: Number(data.depth_score ?? 0),
            depthLevel: data.depth_level ?? '',
            theories: data.theory_guidance || data.theories || [],
          })
        },
        onError: (msg) => {
          ElMessage.error(msg || '生成失败')
        }
      }
    )
  } catch (e) {
    // 流式中途异常（如已通过 onError 提示），这里兜底
    if (!latestGuidance.value) {
      ElMessage.error('生成失败，请重试')
    }
  } finally {
    generating.value = false
  }
}

/** 暴露给父组件的方法和状态 */
defineExpose({
  reflectionId,
  content,
  depthHistory,
  save,
})
</script>

<style scoped>
.mb8 {
  margin-bottom: 8px;
}
.mb12 {
  margin-bottom: 12px;
}
.tab-actions {
  display: flex;
  gap: 8px;
}
.stream-preview {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 12px 14px;
  margin-bottom: 12px;
}
.stream-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
  max-height: 320px;
  overflow: auto;
}
.stream-text .cursor {
  animation: blink 1s steps(1) infinite;
  color: #409eff;
}
@keyframes blink {
  50% { opacity: 0; }
}
.inline-guidance .section {
  margin-bottom: 14px;
}
.inline-guidance .section:last-child {
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
