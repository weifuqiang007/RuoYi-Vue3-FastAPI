<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="14">
        <el-alert
          v-if="keyEvents.length === 0"
          title="尚未获取到关键事件，请先在情境区进行 AI 分析。"
          type="warning"
          :closable="false"
          show-icon
          class="mb8"
        />

        <DecisionForm v-model="currentDecision" :key-events="keyEvents">
          <template #actions>
            <el-button :loading="saving" @click="save">保存</el-button>
            <el-button type="success" :loading="confirming" @click="confirm">确认并进入反思区</el-button>
          </template>
        </DecisionForm>

        <div class="mb8" />

        <el-card shadow="never">
          <template #header>
            <div class="header">
              <span>我的决策记录（{{ decisionList.length }}）</span>
              <div class="actions">
                <el-button size="small" icon="Refresh" @click="loadDecisionList">刷新</el-button>
                <el-button size="small" @click="newDecision">新建</el-button>
              </div>
            </div>
          </template>

          <el-table :data="decisionList" size="small">
            <el-table-column label="当前" width="70" align="center">
              <template #default="scope">
                <el-radio :model-value="activeDecisionId" :value="scope.row.decision_id" @change="selectDecision(scope.row)" />
              </template>
            </el-table-column>
            <el-table-column label="事件" width="90" align="center">
              <template #default="scope">
                {{ (Number(scope.row.key_event_index) + 1) || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="行动" prop="action_taken" min-width="160" show-overflow-tooltip />
            <el-table-column label="操作" width="180" align="center">
              <template #default="scope">
                <el-button link type="primary" icon="Edit" @click="selectDecision(scope.row)">编辑</el-button>
                <el-button link type="danger" icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="10">
        <EthicsPanel :decision-id="activeDecisionId" v-model:analysis="ethicsAnalysis" />
        <div class="mb8" />
        <AlternativeView />
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="LearningDecision">
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getScenarioDetail } from '@/api/learning/scenario'
import { confirmDecision, deleteDecision, listDecision, saveDecision } from '@/api/learning/decision'
import { advanceRecordStage, getRecordDetail } from '@/api/learning/record'
import DecisionForm from './components/DecisionForm.vue'
import EthicsPanel from './components/EthicsPanel.vue'
import AlternativeView from './components/AlternativeView.vue'

const props = defineProps({
  recordId: { type: [String, Number], required: true },
  record: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['stage-updated'])

const route = useRoute()
const router = useRouter()

const scenarioId = computed(() => props.record?.scenario_id ?? props.record?.scenarioId ?? null)
const keyEvents = ref([])

const decisionList = ref([])
const currentDecision = ref({})
const ethicsAnalysis = ref(null)

const saving = ref(false)
const confirming = ref(false)

const activeDecisionId = computed(() => currentDecision.value?.decision_id ?? currentDecision.value?.decisionId ?? null)

async function loadKeyEvents() {
  const res = await getScenarioDetail(props.recordId)
  const data = res.data || {}
  keyEvents.value = data.key_events ?? data.keyEvents ?? []
}

function normalizeDecisionRow(row) {
  return {
    decision_id: row.decision_id ?? row.decisionId,
    key_event_index: row.key_event_index ?? row.keyEventIndex,
    key_event_desc: row.key_event_desc ?? row.keyEventDesc,
    is_intervened: row.is_intervened ?? row.isIntervened,
    action_taken: row.action_taken ?? row.actionTaken,
    reasoning: row.reasoning,
    psychological_state: row.psychological_state ?? row.psychologicalState,
    alternatives: row.alternatives,
    expected_outcome: row.expected_outcome ?? row.expectedOutcome,
    actual_outcome: row.actual_outcome ?? row.actualOutcome,
    ethics_analysis: row.ethics_analysis ?? row.ethicsAnalysis,
    create_time: row.create_time ?? row.createTime,
    update_time: row.update_time ?? row.updateTime,
    is_current: row.is_current ?? row.isCurrent ?? false,
    record_id: row.record_id ?? row.recordId,
    scenario_id: row.scenario_id ?? row.scenarioId ?? scenarioId.value
  }
}

function getDecisionSortTime(row) {
  return row?.update_time || row?.create_time || ''
}

function getDefaultDecision(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return null
  const current = rows.find(item => item.is_current)
  if (current) return current
  return [...rows].sort((a, b) => {
    const timeA = new Date(getDecisionSortTime(a) || 0).getTime()
    const timeB = new Date(getDecisionSortTime(b) || 0).getTime()
    return timeB - timeA
  })[0]
}

async function loadDecisionList() {
  const res = await listDecision(props.recordId)
  const rows = res.data || []
  const normalizedRows = Array.isArray(rows) ? rows.map(normalizeDecisionRow) : []
  decisionList.value = normalizedRows
  const fallbackDecisionId = activeDecisionId.value
  const matched = normalizedRows.find(item => item.decision_id === fallbackDecisionId)
  const target = matched || getDefaultDecision(normalizedRows)
  if (target) {
    applySelectedDecision(target)
    return
  }
  newDecision()
}

function applySelectedDecision(row) {
  currentDecision.value = normalizeDecisionRow(row)
  ethicsAnalysis.value = currentDecision.value.ethics_analysis || null
}

async function selectDecision(row) {
  applySelectedDecision(row)
  decisionList.value = decisionList.value.map(item => ({
    ...item,
    is_current: item.decision_id === row.decision_id
  }))
}

function newDecision() {
  currentDecision.value = {
    decision_id: undefined,
    key_event_index: null,
    key_event_desc: '',
    is_intervened: true,
    action_taken: '',
    reasoning: '',
    psychological_state: '',
    alternatives: '',
    expected_outcome: '',
    actual_outcome: ''
  }
  ethicsAnalysis.value = null
}

async function persistDecision(showMessage) {
  const payload = {
    record_id: props.recordId,
    scenario_id: scenarioId.value,
    ...currentDecision.value,
    is_current: true
  }
  const res = await saveDecision(payload)
  const data = res.data || {}
  const decisionId = data.decision_id ?? data.decisionId ?? currentDecision.value.decision_id
  currentDecision.value = { ...currentDecision.value, decision_id: decisionId, is_current: true }
  if (showMessage) ElMessage.success('保存成功')
}

async function save() {
  saving.value = true
  try {
    await persistDecision(true)
    await loadDecisionList()
    emit('stage-updated')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确认删除这条决策记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteDecision(row.decision_id)
    ElMessage.success('删除成功')
    await loadDecisionList()
  } catch (e) {
    if (e === 'cancel' || e === 'close') return
  }
}

async function confirm() {
  confirming.value = true
  try {
    await persistDecision(false)
    await confirmDecision(props.recordId)
    await advanceRecordStage(props.recordId)
    const res = await getRecordDetail(props.recordId)
    const data = res.data || {}
    const nextStage = data.current_stage ?? data.currentStage
    if (nextStage) {
      router.replace({ query: { ...route.query, stage: String(nextStage) } })
    }
    ElMessage.success('已保存并推进')
    emit('stage-updated')
  } finally {
    confirming.value = false
  }
}

onMounted(async () => {
  await loadKeyEvents()
  await loadDecisionList()
})
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
</style>
