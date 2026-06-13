<template>
  <div class="scenario-page">
    <el-alert
      v-if="presetScenario"
      title="教师预设情境（可在此基础上补充）"
      type="info"
      :closable="false"
      show-icon
      class="mb8"
    >
      <template #default>
        <div style="white-space: pre-wrap">{{ presetScenario }}</div>
      </template>
    </el-alert>

    <el-row :gutter="16">
      <el-col :span="14">
        <ScenarioEditor v-model="description" @blur="handleBlurSave">
          <template #actions>
            <el-button :loading="saving" @click="save">保存</el-button>
            <el-button type="primary" :loading="analyzing" @click="analyze">AI 分析</el-button>
            <el-button type="success" :loading="confirming" @click="confirm">确认并进入决策区</el-button>
          </template>
        </ScenarioEditor>

        <!-- 流式分析过程展示区 -->
        <el-card v-if="analyzeStatus || analyzeStreamText" shadow="never" class="stream-card">
          <template #header>
            <div class="stream-header">
              <span>{{ analyzeStatus || '分析完成' }}</span>
              <el-icon v-if="analyzing" class="is-loading"><Loading /></el-icon>
            </div>
          </template>
          <div v-if="analyzeStreamText" class="stream-content">
            <pre class="stream-text">{{ analyzeStreamText }}</pre>
          </div>
          <div v-else class="stream-empty">等待 AI 输出...</div>
        </el-card>

        <div class="mb8" />

        <KeyEventTimeline v-model:events="keyEvents" @update:events="onEventsChange" />
        <div class="mb8" />
        <ProblemCard v-model:problems="identifiedProblems" @update:problems="onProblemsChange" />
      </el-col>

      <el-col :span="10">
        <AiFollowupPanel :scenario-id="scenarioId" />
        <div class="mb8" />
        <el-card shadow="never">
          <template #header>
            <div class="module-title">
              <span class="bar" />
              <span class="text">分类标签</span>
            </div>
          </template>
          <div v-if="categoryTags.length === 0" class="empty">暂无</div>
          <div v-else class="tag-wrap">
            <el-tag v-for="(t, idx) in categoryTags" :key="idx" class="tag-item">{{ formatTag(t) }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="LearningScenario">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { confirmScenario, getScenarioDetail, saveScenario } from '@/api/learning/scenario'
import { advanceRecordStage } from '@/api/learning/record'
import { analyzeScenarioStream } from '@/api/learning/scenario'
import ScenarioEditor from './components/ScenarioEditor.vue'
import KeyEventTimeline from './components/KeyEventTimeline.vue'
import ProblemCard from './components/ProblemCard.vue'
import AiFollowupPanel from './components/AiFollowupPanel.vue'

const props = defineProps({
  recordId: { type: [String, Number], required: true },
  record: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['stage-updated'])

const scenarioId = ref(null)
const description = ref('')
const keyEvents = ref([])
const identifiedProblems = ref([])
const categoryTags = ref([])

const saving = ref(false)
const analyzing = ref(false)
const confirming = ref(false)

// 流式分析状态
const analyzeStatus = ref('')
const analyzeStreamText = ref('')
let abortController = null

const presetScenario = computed(() => props.record?.preset_scenario ?? props.record?.presetScenario ?? '')

function fillPresetScenarioIfEmpty() {
  if (!description.value?.trim() && presetScenario.value) {
    description.value = presetScenario.value
  }
}

async function loadDetail() {
  const res = await getScenarioDetail(props.recordId)
  const data = res.data || {}
  scenarioId.value = data.scenario_id ?? data.scenarioId ?? props.record?.scenario_id ?? props.record?.scenarioId ?? null
  const loadedDescription = data.description ?? ''
  // 如果后端无已保存的描述，且有教师预设情境，则回填到编辑器
  description.value = loadedDescription || ''
  fillPresetScenarioIfEmpty()
  keyEvents.value = data.key_events ?? data.keyEvents ?? []
  identifiedProblems.value = data.identified_problems ?? data.identifiedProblems ?? []
  categoryTags.value = data.category_tags ?? data.categoryTags ?? []
}

async function save() {
  saving.value = true
  try {
    const res = await saveScenario({
      record_id: props.recordId,
      scenario_id: scenarioId.value,
      description: description.value
    })
    const data = res.data || {}
    scenarioId.value = scenarioId.value ?? data.scenario_id ?? data.scenarioId ?? null
    ElMessage.success('保存成功')
    emit('stage-updated')
  } finally {
    saving.value = false
  }
}

async function analyze() {
  analyzing.value = true
  analyzeStatus.value = '准备分析...'
  analyzeStreamText.value = ''
  abortController = new AbortController()

  try {
    if (!scenarioId.value) {
      await save()
    }

    await analyzeScenarioStream(
      { scenario_id: scenarioId.value },
      {
        onStatus(msg) {
          analyzeStatus.value = msg
        },
        onContent(text) {
          analyzeStreamText.value += text
        },
        onResult(data) {
          keyEvents.value = data.key_events ?? data.keyEvents ?? keyEvents.value
          identifiedProblems.value = data.identified_problems ?? data.identifiedProblems ?? identifiedProblems.value
          categoryTags.value = data.category_tags ?? data.categoryTags ?? categoryTags.value
          analyzeStatus.value = '分析完成'
          ElMessage.success('AI 分析完成')
          emit('stage-updated')
        },
        onError(msg) {
          ElMessage.error('分析失败：' + msg)
          analyzeStatus.value = '分析失败'
        }
      },
      abortController.signal
    )
  } catch (err) {
    if (err?.name !== 'AbortError') {
      ElMessage.error('请求失败：' + (err?.message || '未知错误'))
      analyzeStatus.value = '请求失败'
    }
  } finally {
    analyzing.value = false
    abortController = null
  }
}

async function confirm() {
  confirming.value = true
  try {
    if (!scenarioId.value) {
      await save()
    }
    await confirmScenario({ record_id: props.recordId, scenario_id: scenarioId.value })

    // 推进记录状态机：情景区 → 决策区
    const currentStage = props.record?.current_stage ?? props.record?.currentStage
    const isOngoing = !['submitted', 'completed'].includes(String(currentStage))
    if (isOngoing) {
      await advanceRecordStage(props.recordId)
    }

    ElMessage.success('已保存并推进到决策区')

    // 清除 URL 中的 stage 参数，让 ZoneMain.reload() 使用后端返回的真实阶段
    const route = useRoute()
    const router = useRouter()
    const { stage: _stage, ...restQuery } = route.query
    await router.replace({ query: restQuery })

    emit('stage-updated')
  } finally {
    confirming.value = false
  }
}

function handleBlurSave() {
  if (!description.value?.trim()) return
  save()
}

async function onEventsChange(newEvents) {
  keyEvents.value = newEvents
  await saveScenarioData()
}

async function onProblemsChange(newProblems) {
  identifiedProblems.value = newProblems
  await saveScenarioData()
}

async function saveScenarioData() {
  try {
    const res = await saveScenario({
      record_id: props.recordId,
      scenario_id: scenarioId.value,
      key_events: keyEvents.value,
      identified_problems: identifiedProblems.value
    })
    const data = res.data || {}
    scenarioId.value = scenarioId.value ?? data.scenario_id ?? data.scenarioId ?? null
  } catch {
    ElMessage.error('自动保存失败')
  }
}

function formatTag(t) {
  const obj = normalizeMaybeJson(t)
  if (typeof obj === 'string') return obj
  return obj?.label ?? obj?.name ?? (obj ? JSON.stringify(obj) : '')
}

function normalizeMaybeJson(v) {
  if (!v) return ''
  if (typeof v !== 'string') return v
  const s = v.trim()
  if (!s) return ''
  if (s.startsWith('{') && s.endsWith('}')) {
    try {
      return JSON.parse(s)
    } catch {
      return s
    }
  }
  return s
}

onMounted(() => {
  loadDetail()
})

watch(presetScenario, () => {
  fillPresetScenarioIfEmpty()
})
</script>

<style scoped>
.scenario-page {
  background: #f9fafb;
}
.module-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
}
.bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: #3b82f6;
}
.empty {
  color: #909399;
  padding: 14px 0;
  text-align: center;
}
.tag-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tag-item {
  margin: 0;
}
.stream-card {
  margin-top: 12px;
}
.stream-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #409eff;
}
.stream-content {
  max-height: 300px;
  overflow-y: auto;
}
.stream-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
  color: #303133;
}
.stream-empty {
  color: #909399;
  text-align: center;
  padding: 12px 0;
}
</style>
