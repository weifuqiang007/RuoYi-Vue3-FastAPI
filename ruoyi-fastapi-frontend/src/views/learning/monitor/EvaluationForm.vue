<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="选择任务" prop="taskId">
        <el-select v-model="queryParams.taskId" placeholder="请选择教学任务" clearable style="width: 300px" @change="loadStudents">
          <el-option v-for="t in taskOptions" :key="t.task_id" :label="t.task_name" :value="t.task_id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="loadStudents">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="studentList">
      <el-table-column label="用户ID" prop="user_id" width="90" />
      <el-table-column label="当前阶段" width="100" align="center">
        <template #default="scope">
          <el-tag :type="stageTagType(scope.row.current_stage)" size="small">{{ stageLabel(scope.row.current_stage) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'completed' ? 'success' : 'info'" size="small">
            {{ scope.row.status === 'submitted' ? '待评价' : scope.row.status === 'completed' ? '已评价' : '进行中' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="primary" link size="small" @click="openEvaluate(scope.row)"
            :disabled="scope.row.status !== 'submitted' && scope.row.status !== 'completed'">
            {{ scope.row.status === 'completed' ? '查看评价' : '评价' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 评价弹窗 -->
    <el-dialog :title="evalMode === 'view' ? '评价详情' : '提交评价'" v-model="evalVisible" width="640px">
      <el-form :model="evalForm" label-width="100px" :disabled="evalMode === 'view'">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="情境区分数">
              <el-input-number v-model="evalForm.scenario_score" :min="0" :max="100" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="决策区分数">
              <el-input-number v-model="evalForm.decision_score" :min="0" :max="100" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="反思区分数">
              <el-input-number v-model="evalForm.reflection_score" :min="0" :max="100" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="研究区分数">
              <el-input-number v-model="evalForm.research_score" :min="0" :max="100" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="情境区评语">
          <el-input v-model="evalForm.scenario_feedback" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="决策区评语">
          <el-input v-model="evalForm.decision_feedback" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="反思区评语">
          <el-input v-model="evalForm.reflection_feedback" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="研究区评语">
          <el-input v-model="evalForm.research_feedback" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="总评语">
          <el-input v-model="evalForm.overall_feedback" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer v-if="evalMode === 'edit'">
        <el-button @click="evalVisible = false">取 消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitEval">提交评价</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="EvaluationForm">
import { ElMessage } from 'element-plus'
import { listTeacherTask } from '@/api/learning/task'
import { getClassOverview, submitEvaluation, getEvaluationDetail } from '@/api/learning/monitor'

const loading = ref(false)
const showSearch = ref(true)
const studentList = ref([])
const taskOptions = ref([])

const queryParams = ref({ taskId: undefined })

const evalVisible = ref(false)
const evalMode = ref('edit')
const submitting = ref(false)
const currentRecordId = ref(null)

const evalForm = ref({
  scenario_score: null,
  decision_score: null,
  reflection_score: null,
  research_score: null,
  scenario_feedback: '',
  decision_feedback: '',
  reflection_feedback: '',
  research_feedback: '',
  overall_feedback: ''
})

function stageLabel(stage) {
  const key = String(stage || '')
  return { scenario: '情境', decision: '决策', reflection: '反思', research: '研究', submitted: '已提交', completed: '已完成' }[key] || key
}

function stageTagType(stage) {
  const key = String(stage || '')
  return { scenario: 'info', decision: 'warning', reflection: 'primary', research: 'success', submitted: 'success', completed: 'success' }[key] || 'info'
}

async function loadTaskOptions() {
  const res = await listTeacherTask({ pageNum: 1, pageSize: 100, status: '1' })
  const data = res?.data ?? {}
  const rows = Array.isArray(data.rows) ? data.rows : Array.isArray(res?.rows) ? res.rows : []
  taskOptions.value = rows.map(r => ({
    task_id: r.task_id ?? r.taskId,
    task_name: r.task_name ?? r.taskName
  }))
}

function loadStudents() {
  if (!queryParams.value.taskId) return
  loading.value = true
  getClassOverview(queryParams.value.taskId)
    .then(res => {
      const data = res?.data ?? {}
      studentList.value = (data.students || []).filter(s => s.status === 'submitted' || s.status === 'completed')
    })
    .finally(() => { loading.value = false })
}

async function openEvaluate(row) {
  currentRecordId.value = row.record_id
  if (row.status === 'completed') {
    evalMode.value = 'view'
    const res = await getEvaluationDetail(row.record_id)
    const d = res?.data ?? {}
    evalForm.value = {
      scenario_score: d.scenario_score,
      decision_score: d.decision_score,
      reflection_score: d.reflection_score,
      research_score: d.research_score,
      scenario_feedback: d.scenario_feedback || '',
      decision_feedback: d.decision_feedback || '',
      reflection_feedback: d.reflection_feedback || '',
      research_feedback: d.research_feedback || '',
      overall_feedback: d.overall_feedback || ''
    }
  } else {
    evalMode.value = 'edit'
    evalForm.value = {
      scenario_score: null, decision_score: null, reflection_score: null, research_score: null,
      scenario_feedback: '', decision_feedback: '', reflection_feedback: '', research_feedback: '', overall_feedback: ''
    }
  }
  evalVisible.value = true
}

async function submitEval() {
  submitting.value = true
  try {
    await submitEvaluation({ record_id: currentRecordId.value, ...evalForm.value })
    ElMessage.success('评价提交成功')
    evalVisible.value = false
    loadStudents()
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadTaskOptions()
})
</script>
