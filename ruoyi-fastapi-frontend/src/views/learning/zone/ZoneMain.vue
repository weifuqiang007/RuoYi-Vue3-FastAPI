<template>
  <div class="app-container">
    <el-card shadow="never" class="mb8">
      <div class="zone-header">
        <div class="zone-title">
          <div class="title-main">{{ headerTitle }}</div>
          <div class="title-sub">记录ID：{{ recordId || '-' }}</div>
        </div>
        <div class="zone-actions">
          <el-button icon="Refresh" @click="reload">刷新</el-button>
          <el-tag v-if="isSubmittedStage" type="warning" effect="plain">{{ stageLabel(recordStage) }}</el-tag>
          <el-button
            v-else
            type="primary"
            icon="Right"
            :loading="advancing"
            @click="advance"
          >
            推进到下一区
          </el-button>
        </div>
      </div>
    </el-card>

    <el-alert
      v-if="isBrowsingHistory"
      :title="`当前正在查看 ${stageLabel(visibleStage)}，真实进度是 ${stageLabel(recordStage)}`"
      type="warning"
      :closable="false"
      show-icon
      class="mb8"
    />

    <ZoneNavigator :current-stage="visibleStage" @select="handleStageSelect" class="mb8" />

    <el-alert
      v-if="isSubmittedStage"
      :title="submittedStageTip"
      type="success"
      :closable="false"
      show-icon
      class="mb8"
    />

    <component
      :is="stageComponent"
      v-if="recordId && stageComponent"
      :record-id="recordId"
      :record="record"
      @stage-updated="reload"
    />
  </div>
</template>

<script setup name="ZoneMain">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import ZoneNavigator from '@/views/learning/components/ZoneNavigator.vue'
import { advanceRecordStage, getRecordDetail } from '@/api/learning/record'

import ScenarioPage from '@/views/learning/scenario/index.vue'
import DecisionPage from '@/views/learning/decision/index.vue'
import ReflectionPage from '@/views/learning/reflection/index.vue'
import ResearchPage from '@/views/learning/research/index.vue'

const route = useRoute()
const router = useRouter()

const zoneStages = ['scenario', 'decision', 'reflection', 'research']
const submittedStages = ['submitted', 'completed']
const stageNames = {
  scenario: '情境区',
  decision: '决策区',
  reflection: '反思区',
  research: '研究生成区',
  submitted: '已提交',
  completed: '已完成'
}

const recordId = computed(() => {
  const id = route.query.record_id ?? route.query.recordId ?? route.params.record_id ?? route.params.recordId
  return id ? String(id) : ''
})

const record = ref({})
const advancing = ref(false)
const visibleStage = ref('scenario')

const recordStage = computed(() => {
  const stage = record.value?.current_stage ?? record.value?.currentStage
  return stage ? String(stage) : 'scenario'
})

const isSubmittedStage = computed(() => submittedStages.includes(recordStage.value))
const isBrowsingHistory = computed(() => (
  zoneStages.includes(visibleStage.value) &&
  zoneStages.includes(recordStage.value) &&
  visibleStage.value !== recordStage.value
))
const submittedStageTip = computed(() => {
  if (recordStage.value === 'completed') return '当前记录已完成评价。'
  return '当前记录已提交，等待教师评价。'
})

const headerTitle = computed(() => {
  const name = record.value?.task_name ?? record.value?.taskName
  return name ? `反身性研究：${name}` : '反身性研究'
})

const stageComponent = computed(() => {
  const map = {
    scenario: ScenarioPage,
    decision: DecisionPage,
    reflection: ReflectionPage,
    research: ResearchPage
  }
  return map[visibleStage.value] || null
})

function handleStageSelect(stage) {
  visibleStage.value = stage
  router.replace({ query: { ...route.query, stage } })
}

function stageLabel(stage) {
  return stageNames[stage] || stage || '-'
}

function syncVisibleStage(stage) {
  if (zoneStages.includes(stage)) {
    visibleStage.value = stage
    if (route.query.stage !== stage) {
      router.replace({ query: { ...route.query, stage } })
    }
    return
  }

  visibleStage.value = stage
  if (route.query.stage) {
    const { stage: _stage, ...query } = route.query
    router.replace({ query })
  }
}

async function reload() {
  if (!recordId.value) return
  const res = await getRecordDetail(recordId.value)
  record.value = res.data || {}
  syncVisibleStage(recordStage.value)
}

async function advance() {
  if (!recordId.value) return
  if (isSubmittedStage.value) {
    ElMessage.warning(`已是${stageLabel(recordStage.value)}状态，无需继续推进`)
    return
  }
  if (visibleStage.value !== recordStage.value) {
    ElMessage.warning(`当前查看区与真实进度不一致，已切回到${stageLabel(recordStage.value)}`)
    syncVisibleStage(recordStage.value)
    return
  }

  advancing.value = true
  try {
    await advanceRecordStage(recordId.value)
    ElMessage.success('已推进')
    await reload()
  } finally {
    advancing.value = false
  }
}

onMounted(() => {
  reload()
})
</script>

<style scoped>
.zone-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
.zone-title .title-main {
  font-size: 16px;
  font-weight: 600;
}
.zone-title .title-sub {
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
}
.zone-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
