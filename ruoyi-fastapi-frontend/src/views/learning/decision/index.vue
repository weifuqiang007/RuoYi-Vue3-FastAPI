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
            <el-table-column label="ID" prop="decision_id" width="80" />
            <el-table-column label="事件" width="90" align="center">
              <template #default="scope">
                {{ (Number(scope.row.key_event_index) + 1) || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="行动" prop="action_taken" min-width="160" show-overflow-tooltip />
            <el-table-column label="操作" width="120" align="center">
              <template #default="scope">
                <el-button link type="primary" icon="Edit" @click="selectDecision(scope.row)">编辑</el-button>
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
import { ElMessage } from 'element-plus'
import { getScenarioDetail } from '@/api/learning/scenario'
import { confirmDecision, listDecision, saveDecision } from '@/api/learning/decision'
import DecisionForm from './components/DecisionForm.vue'
import EthicsPanel from './components/EthicsPanel.vue'
import AlternativeView from './components/AlternativeView.vue'

const props = defineProps({
  recordId: { type: [String, Number], required: true },
  record: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['stage-updated'])

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
    ethics_analysis: row.ethics_analysis ?? row.ethicsAnalysis
  }
}

async function loadDecisionList() {
  const res = await listDecision(props.recordId)
  const rows = res.data || []
  decisionList.value = Array.isArray(rows) ? rows.map(normalizeDecisionRow) : []
}

function selectDecision(row) {
  currentDecision.value = normalizeDecisionRow(row)
  ethicsAnalysis.value = currentDecision.value.ethics_analysis || null
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

async function save() {
  saving.value = true
  try {
    const payload = {
      record_id: props.recordId,
      scenario_id: scenarioId.value,
      ...currentDecision.value
    }
    const res = await saveDecision(payload)
    const data = res.data || {}
    const decisionId = data.decision_id ?? data.decisionId ?? currentDecision.value.decision_id
    currentDecision.value = { ...currentDecision.value, decision_id: decisionId }
    ElMessage.success('保存成功')
    await loadDecisionList()
    emit('stage-updated')
  } finally {
    saving.value = false
  }
}

async function confirm() {
  confirming.value = true
  try {
    await confirmDecision(props.recordId)
    ElMessage.success('已确认')
    emit('stage-updated')
  } finally {
    confirming.value = false
  }
}

onMounted(async () => {
  await loadKeyEvents()
  await loadDecisionList()
  newDecision()
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

