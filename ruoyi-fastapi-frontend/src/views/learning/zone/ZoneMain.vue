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
          <el-button type="primary" icon="Right" :loading="advancing" @click="advance">推进到下一区</el-button>
        </div>
      </div>
    </el-card>

    <ZoneNavigator :current-stage="currentStage" @select="handleStageSelect" class="mb8" />

    <component
      :is="stageComponent"
      v-if="recordId"
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

const recordId = computed(() => {
  const id = route.query.record_id ?? route.query.recordId ?? route.params.record_id ?? route.params.recordId
  return id ? String(id) : ''
})

const record = ref({})
const advancing = ref(false)

const currentStage = computed(() => {
  const q = route.query.stage
  if (q) return String(q)
  const stage = record.value?.current_stage ?? record.value?.currentStage
  return stage ? String(stage) : 'scenario'
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
  return map[currentStage.value] || ScenarioPage
})

function handleStageSelect(stage) {
  router.replace({ query: { ...route.query, stage } })
}

async function reload() {
  if (!recordId.value) return
  const res = await getRecordDetail(recordId.value)
  record.value = res.data || {}
}

async function advance() {
  if (!recordId.value) return
  advancing.value = true
  try {
    await advanceRecordStage(recordId.value)
    ElMessage.success('已推进')
    await reload()
    const nextStage = record.value?.current_stage ?? record.value?.currentStage
    if (nextStage) {
      router.replace({ query: { ...route.query, stage: String(nextStage) } })
    }
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
</style>

