<template>
  <div>
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

        <div class="mb8" />

        <KeyEventTimeline :events="keyEvents" />
        <div class="mb8" />
        <ProblemCard :problems="identifiedProblems" />
      </el-col>

      <el-col :span="10">
        <AiFollowupPanel :scenario-id="scenarioId" />
        <div class="mb8" />
        <el-card shadow="never">
          <template #header>分类标签</template>
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
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { analyzeScenario, confirmScenario, getScenarioDetail, saveScenario } from '@/api/learning/scenario'
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

const presetScenario = computed(() => props.record?.preset_scenario ?? props.record?.presetScenario ?? '')

async function loadDetail() {
  const res = await getScenarioDetail(props.recordId)
  const data = res.data || {}
  scenarioId.value = data.scenario_id ?? data.scenarioId ?? props.record?.scenario_id ?? props.record?.scenarioId ?? null
  description.value = data.description ?? ''
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
  try {
    if (!scenarioId.value) {
      await save()
    }
    const res = await analyzeScenario({
      record_id: props.recordId,
      scenario_id: scenarioId.value
    })
    const data = res.data || {}
    keyEvents.value = data.key_events ?? data.keyEvents ?? keyEvents.value
    identifiedProblems.value = data.identified_problems ?? data.identifiedProblems ?? identifiedProblems.value
    categoryTags.value = data.category_tags ?? data.categoryTags ?? categoryTags.value
    ElMessage.success('分析完成')
    emit('stage-updated')
  } finally {
    analyzing.value = false
  }
}

async function confirm() {
  confirming.value = true
  try {
    if (!scenarioId.value) {
      await save()
    }
    await confirmScenario({ record_id: props.recordId, scenario_id: scenarioId.value })
    ElMessage.success('已确认')
    emit('stage-updated')
  } finally {
    confirming.value = false
  }
}

function handleBlurSave() {
  if (!description.value?.trim()) return
  save()
}

function formatTag(t) {
  if (typeof t === 'string') return t
  if (t?.label) return t.label
  return JSON.stringify(t)
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
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
</style>

