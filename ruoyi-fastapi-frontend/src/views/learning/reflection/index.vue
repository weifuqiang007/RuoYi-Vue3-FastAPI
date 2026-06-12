<template>
  <div>
    <DepthIndicator :depth-score="depthScore" :depth-level="depthLevel" class="mb8" />

    <!-- 多轮反思时间线 -->
    <div class="round-timeline mb8">
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
      />

      <!-- 当前轮次：编辑 + AI 指导 -->
      <el-card shadow="hover" class="round-card current-round mb8">
        <template #header>
          <div class="round-header">
            <div class="round-title">
              <el-tag type="primary" size="small" effect="dark">
                第 {{ historyRounds.length + 1 }} 轮（编辑中）
              </el-tag>
            </div>
            <div class="round-actions">
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
          </div>
        </template>

        <!-- 反思编辑器 -->
        <el-input
          v-model="content"
          type="textarea"
          :rows="8"
          placeholder="基于上轮的理论指导，继续深化你的反思：发生了什么？为什么？你在其中的立场、价值与关系是什么？"
          class="mb12"
        />

        <!-- 最新一轮 AI 指导（内联展示） -->
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
              <div v-if="g.description && !g.relevance && !g.suggestion" class="theory-desc">
                {{ g.description }}
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
      </el-card>
    </div>

    <!-- 深度演变折线图 + 理论总览 + 操作按钮 -->
    <el-row :gutter="16">
      <el-col :span="14">
        <DepthChart :history="depthHistory" />
      </el-col>
      <el-col :span="10">
        <TheoryLinkage :theories="theories" />
        <div class="mb8" />
        <el-card shadow="never">
          <el-button
            type="success"
            :loading="confirming"
            style="width: 100%"
            @click="confirm"
          >
            确认并进入研究区
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="LearningReflection">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, MagicStick } from '@element-plus/icons-vue'
import { confirmReflection, getReflectionDepthHistory, getReflectionDetail, saveReflection, generateReflectionQuestions } from '@/api/learning/reflection'
import { advanceRecordStage, getRecordDetail } from '@/api/learning/record'
import DepthIndicator from './components/DepthIndicator.vue'
import ReflectionRoundCard from './components/ReflectionRoundCard.vue'
import DepthChart from './components/DepthChart.vue'
import TheoryLinkage from './components/TheoryLinkage.vue'

const props = defineProps({
  recordId: { type: [String, Number], required: true },
  record: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['stage-updated'])

const route = useRoute()
const router = useRouter()

const reflectionId = ref(null)
const content = ref('')

const depthScore = ref(0)
const depthLevel = ref('')

const theories = ref([])
const depthHistory = ref([])

/** 存储所有 assistant 对话（历史轮次） */
const dialogues = ref([])

/** 最新一轮 AI 指导结果 */
const latestGuidance = ref(null)

const saving = ref(false)
const generating = ref(false)
const confirming = ref(false)

/** 历史轮次 = 所有 assistant 对话（排除最新一条如果还未保存反思文本） */
const historyRounds = computed(() => {
  return dialogues.value
    .filter(d => d.role === 'assistant')
    .map((d, idx) => {
      return {
        content: d.content,
        depthScoreAfter: d.depth_score_after ?? d.depthScoreAfter ?? null,
        depthScoreBefore: d.depth_score_before ?? d.depthScoreBefore ?? null,
        createTime: d.create_time ?? d.createTime ?? '',
        index: idx,
      }
    })
})

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

async function loadDetail() {
  const res = await getReflectionDetail(props.recordId)
  const data = res.data || {}
  reflectionId.value = data.reflection_id ?? data.reflectionId ?? null
  content.value = data.content ?? ''
  depthScore.value = Number(data.depth_score ?? data.depthScore ?? 0)
  depthLevel.value = data.depth_level ?? data.depthLevel ?? ''
  theories.value = normalizeArray(data.linked_theories ?? data.theories ?? [])
  dialogues.value = normalizeArray(data.dialogues ?? [])

  // 从最后一条 assistant 对话中恢复 latestGuidance
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

  await loadDepthHistory()
}

async function loadDepthHistory() {
  if (!reflectionId.value) {
    depthHistory.value = []
    return
  }
  const res = await getReflectionDepthHistory(reflectionId.value)
  const data = res.data || []
  depthHistory.value = Array.isArray(data) ? data : []
}

async function save() {
  const ok = await persistReflection(true)
  if (ok) {
    ElMessage.success('保存成功')
    emit('stage-updated')
  }
}

async function persistReflection(showMessage) {
  if (!content.value.trim()) {
    if (showMessage) ElMessage.warning('请先填写反思内容')
    return false
  }
  saving.value = true
  try {
    const res = await saveReflection({
      record_id: props.recordId,
      reflection_id: reflectionId.value,
      content: content.value
    })
    const data = res.data || {}
    if (!reflectionId.value) {
      reflectionId.value = data.reflection_id ?? data.reflectionId ?? null
    }
    if (data.depth_score !== undefined) depthScore.value = Number(data.depth_score)
    if (data.depth_level) depthLevel.value = data.depth_level
    await loadDepthHistory()
    return true
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
  try {
    const res = await generateReflectionQuestions({ reflection_id: reflectionId.value })
    const data = res.data || {}
    latestGuidance.value = data

    // 更新深度
    if (data.depth_score !== undefined) depthScore.value = Number(data.depth_score)
    if (data.depth_level) depthLevel.value = data.depth_level

    // 更新理论
    const newTheories = data.theory_guidance || data.theories || []
    if (Array.isArray(newTheories) && newTheories.length) {
      theories.value = newTheories
    }

    // 刷新对话历史
    await loadDetail()
  } finally {
    generating.value = false
  }
}

async function confirm() {
  confirming.value = true
  try {
    const ok = await persistReflection(false)
    if (!ok) return

    // 判断当前记录状态：已提交/已完成的记录不需要再推进状态机
    const currentStage = props.record?.current_stage ?? props.record?.currentStage
    const isOngoing = !['submitted', 'completed'].includes(String(currentStage))

    if (isOngoing) {
      await confirmReflection({ record_id: props.recordId, reflection_id: reflectionId.value })
      await advanceRecordStage(props.recordId)
    }

    // 无论什么状态，始终跳转到研究生成区
    router.replace({ query: { ...route.query, stage: 'research' } })
    ElMessage.success(isOngoing ? '已保存并推进到研究生成区' : '已跳转到研究生成区')
    emit('stage-updated')
  } finally {
    confirming.value = false
  }
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.mb8 {
  margin-bottom: 8px;
}
.mb12 {
  margin-bottom: 12px;
}
.round-card {
  transition: all 0.2s;
}
.round-card.current-round {
  border-left: 3px solid #409eff;
}
.round-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.round-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.round-actions {
  display: flex;
  gap: 8px;
}

/* 内联指导样式 */
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
