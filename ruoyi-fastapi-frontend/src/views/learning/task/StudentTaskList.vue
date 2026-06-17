<template>
  <div class="app-container">
    <el-alert
      title="这里展示教师发布到你班级的任务。你也可以创建「自研课题」进入四区流程。"
      type="info"
      :closable="false"
      show-icon
      class="mb8"
    />

    <el-form ref="queryRef" :model="queryParams" :inline="true" class="mb8">
      <el-form-item label="任务类型">
        <el-select v-model="queryParams.creator_type" placeholder="全部" clearable style="width: 160px">
          <el-option label="教学任务" value="0" />
          <el-option label="自研课题" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item label="任务名称">
        <el-input
          v-model="queryParams.task_name"
          placeholder="请输入任务名称"
          clearable
          style="width: 220px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="归属班级">
        <el-select v-model="queryParams.dept_id" placeholder="请选择班级" clearable filterable style="width: 220px">
          <el-option v-for="d in deptOptions" :key="d.deptId" :label="d.deptName" :value="d.deptId" />
        </el-select>
      </el-form-item>
      <el-form-item label="发布教师">
        <el-input
          v-model="queryParams.teacher_name"
          placeholder="请输入教师姓名"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="任务简述">
        <el-input
          v-model="queryParams.task_description"
          placeholder="请输入任务简述"
          clearable
          style="width: 220px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="截止时间">
        <el-date-picker
          v-model="deadlineRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 260px"
        />
      </el-form-item>
      <el-form-item label="创建时间">
        <el-date-picker
          v-model="createTimeRange"
          type="daterange"
          value-format="YYYY-MM-DD HH:mm:ss"
          range-separator="-"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          style="width: 340px"
        />
      </el-form-item>
      <el-form-item label="发布状态">
        <el-select v-model="queryParams.status" placeholder="全部" clearable style="width: 160px">
          <el-option label="草稿" value="0" />
          <el-option label="已发布" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="openSelfDialog">新增自研课题</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button icon="Refresh" @click="getList">刷新</el-button>
      </el-col>
    </el-row>

    <el-table v-loading="loading" :data="taskList">
      <el-table-column label="类型" width="100" align="center">
        <template #default="scope">
          <el-tag v-if="String(scope.row.creator_type) === '1'" type="success">自研课题</el-tag>
          <el-tag v-else type="primary">教学任务</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="任务名称" prop="task_name" min-width="200" show-overflow-tooltip />
      <el-table-column label="归属班级" min-width="220">
        <template #default="scope">
          <span
            v-if="scope.row.assigned_classes && scope.row.assigned_classes.length > 0"
            class="class-cell"
            @click="openAssignedClassDialog(scope.row)"
          >
            <span class="class-ellipsis">
              {{ formatAssignedClasses(scope.row.assigned_classes) }}
            </span>
          </span>
          <span v-else style="color: #909399;">-</span>
        </template>
      </el-table-column>
      <el-table-column label="发布教师" width="110" align="center">
        <template #default="scope">
          <span v-if="String(scope.row.creator_type) === '0'">{{ scope.row.teacher_name || '-' }}</span>
          <span v-else style="color: #67c23a;">自研</span>
        </template>
      </el-table-column>
      <el-table-column label="任务简述" prop="task_description" min-width="220" show-overflow-tooltip />
      <el-table-column label="截止时间" prop="deadline" width="170" />
      <el-table-column label="状态" width="90" align="center">
        <template #default="scope">
          <el-tag :type="statusTagType(scope.row.status)">
            {{ statusLabel(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button type="primary" link icon="CaretRight" @click="handleStart(scope.row)">开始</el-button>
          <el-button type="info" link icon="View" @click="openDetail(scope.row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.page_num"
      v-model:limit="queryParams.page_size"
      @pagination="getList"
    />

    <el-dialog title="新增自研课题" v-model="selfDialogVisible" width="680px">
      <el-form label-width="100px">
        <el-form-item label="课题名称" required>
          <el-input v-model="selfTaskName" placeholder="请输入课题名称" />
        </el-form-item>
        <el-form-item label="课题描述">
          <el-input
            v-model="selfTaskDescription"
            type="textarea"
            :rows="4"
            placeholder="请输入课题描述（可选）"
          />
        </el-form-item>

        <el-divider content-position="left">各区知识库配置</el-divider>

        <el-row :gutter="14">
          <el-col :span="12">
            <el-form-item label="情境区KB">
              <el-select
                v-model="selfScenarioKbIds"
                multiple
                filterable
                clearable
                style="width: 100%"
                :loading="kbLoading"
                @visible-change="handleKbVisibleChange"
              >
                <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="决策区KB">
              <el-select
                v-model="selfDecisionKbIds"
                multiple
                filterable
                clearable
                style="width: 100%"
                :loading="kbLoading"
                @visible-change="handleKbVisibleChange"
              >
                <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="14">
          <el-col :span="12">
            <el-form-item label="反思区KB">
              <el-select
                v-model="selfReflectionKbIds"
                multiple
                filterable
                clearable
                style="width: 100%"
                :loading="kbLoading"
                @visible-change="handleKbVisibleChange"
              >
                <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="研究区KB">
              <el-select
                v-model="selfResearchKbIds"
                multiple
                filterable
                clearable
                style="width: 100%"
                :loading="kbLoading"
                @visible-change="handleKbVisibleChange"
              >
                <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="批阅模型">
          <el-select
            v-model="selfReviewModelId"
            filterable
            clearable
            placeholder="不选则使用系统默认批阅模型（须≠学生侧模型）"
            style="width: 100%"
            :loading="modelLoading"
            @visible-change="handleModelVisibleChange"
          >
            <el-option v-for="m in modelOptions" :key="m.model_id" :label="m.model_name" :value="m.model_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="selfDialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="creating" @click="submitSelf">确 定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="任务详情" size="40%">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="任务名称">{{ detail.task_name }}</el-descriptions-item>
        <el-descriptions-item label="任务描述">{{ detail.task_description }}</el-descriptions-item>
        <el-descriptions-item label="预设情境">{{ detail.preset_scenario }}</el-descriptions-item>
        <el-descriptions-item label="截止时间">{{ detail.deadline }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <el-dialog title="归属班级" v-model="assignedClassVisible" width="520px">
      <div v-if="assignedClassList.length === 0" style="color: #909399; text-align: center; padding: 10px 0;">
        暂无
      </div>
      <div v-else>
        <el-tag v-for="c in assignedClassList" :key="c.dept_id ?? c.deptId" class="mr4" style="margin-bottom: 6px;">
          {{ c.dept_name ?? c.deptName }}
        </el-tag>
      </div>
      <template #footer>
        <el-button type="primary" @click="assignedClassVisible = false">关 闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="StudentTaskList">
import { ElMessage } from 'element-plus'
import { listStudentTask, getTaskDetail, createStudentTask } from '@/api/learning/task'
import { startRecord } from '@/api/learning/record'
import { listDept } from '@/api/system/dept'
import { listKnowledgeBase } from '@/api/rag/knowledgeBase'
import { listModelAll } from '@/api/ai/model'

const router = useRouter()

const loading = ref(false)
const taskList = ref([])
const total = ref(0)
const queryRef = ref()
const deptOptions = ref([])
const deadlineRange = ref([])
const createTimeRange = ref([])
const queryParams = reactive({
  page_num: 1,
  page_size: 10,
  creator_type: undefined,
  task_name: undefined,
  dept_id: undefined,
  teacher_name: undefined,
  task_description: undefined,
  status: undefined
})

const selfDialogVisible = ref(false)
const selfTaskName = ref('')
const selfTaskDescription = ref('')
const creating = ref(false)

// 四区知识库配置
const DEFAULT_KB_ID = 5
const kbOptions = ref([])
const kbLoading = ref(false)
const kbLoaded = ref(false)
const selfScenarioKbIds = ref([DEFAULT_KB_ID])
const selfDecisionKbIds = ref([DEFAULT_KB_ID])
const selfReflectionKbIds = ref([DEFAULT_KB_ID])
const selfResearchKbIds = ref([DEFAULT_KB_ID])
const selfReviewModelId = ref(undefined)

// 批阅模型选项
const modelOptions = ref([])
const modelLoading = ref(false)
const modelLoaded = ref(false)

const detailVisible = ref(false)
const detail = ref({})

const assignedClassVisible = ref(false)
const assignedClassList = ref([])

function normalizeTaskRow(row) {
  const creatorType = row.creator_type ?? row.creatorType
  return {
    task_id: row.task_id ?? row.taskId,
    task_name: row.task_name ?? row.taskName,
    task_description: row.task_description ?? row.taskDescription,
    preset_scenario: row.preset_scenario ?? row.presetScenario,
    deadline: row.deadline,
    status: row.status,
    creator_type: creatorType ?? (row.source === 'self_study' ? '1' : '0'),
    student_id: row.student_id ?? row.studentId,
    student_name: row.student_name ?? row.studentName,
    teacher_id: row.teacher_id ?? row.teacherId,
    teacher_name: row.teacher_name ?? row.teacherName,
    assigned_classes: row.assigned_classes ?? row.assignedClasses ?? [],
    source: row.source
  }
}

function statusLabel(v) {
  const key = String(v ?? '')
  return { '0': '草稿', '1': '已发布', '2': '已关闭' }[key] || '未知'
}

function statusTagType(v) {
  const key = String(v ?? '')
  return { '0': 'info', '1': 'success', '2': 'warning' }[key] || 'info'
}

function formatAssignedClasses(list) {
  if (!Array.isArray(list) || list.length === 0) return ''
  return list.map(c => c.dept_name ?? c.deptName ?? '').filter(Boolean).join('、')
}

function openAssignedClassDialog(row) {
  assignedClassList.value = Array.isArray(row?.assigned_classes) ? row.assigned_classes : []
  assignedClassVisible.value = true
}

async function loadDeptOptions() {
  const res = await listDept()
  const data = res?.data
  deptOptions.value = Array.isArray(data) ? data : Array.isArray(data?.rows) ? data.rows : []
}

function buildQueryParams() {
  const params = {
    page_num: queryParams.page_num,
    page_size: queryParams.page_size
  }
  if (queryParams.creator_type) params.creator_type = queryParams.creator_type
  if (queryParams.task_name) params.task_name = queryParams.task_name
  if (queryParams.dept_id !== undefined && queryParams.dept_id !== null && queryParams.dept_id !== '') {
    params.dept_id = queryParams.dept_id
  }
  if (queryParams.teacher_name) params.teacher_name = queryParams.teacher_name
  if (queryParams.task_description) params.task_description = queryParams.task_description
  if (queryParams.status) params.status = queryParams.status
  if (Array.isArray(deadlineRange.value) && deadlineRange.value.length === 2) {
    params.deadline_begin = deadlineRange.value[0]
    params.deadline_end = deadlineRange.value[1]
  }
  if (Array.isArray(createTimeRange.value) && createTimeRange.value.length === 2) {
    params.create_time_begin = createTimeRange.value[0]
    params.create_time_end = createTimeRange.value[1]
  }
  return params
}

function getList() {
  loading.value = true
  listStudentTask(buildQueryParams())
    .then(res => {
      const data = res?.data ?? {}
      const rows = Array.isArray(data.rows) ? data.rows : Array.isArray(res?.rows) ? res.rows : []
      taskList.value = rows.map(normalizeTaskRow)
      total.value = data.total ?? res?.total ?? 0
    })
    .finally(() => {
      loading.value = false
    })
}

function handleQuery() {
  queryParams.page_num = 1
  getList()
}

function resetQuery() {
  deadlineRange.value = []
  createTimeRange.value = []
  queryRef.value?.resetFields?.()
  queryParams.page_num = 1
  queryParams.page_size = 10
  getList()
}

async function handleStart(row) {
  if (!row.task_id) {
    ElMessage.warning('任务ID缺失，无法开始')
    return
  }
  const res = await startRecord(row.task_id)
  const recordId = res?.data?.record_id ?? res?.data?.recordId ?? res?.data?.record_id ?? res?.data
  if (!recordId) {
    ElMessage.success('已开始任务')
    return
  }
  await router.push({ path: '/learning/zone', query: { record_id: recordId } })
}

async function loadKbOptions() {
  if (kbLoading.value) return
  kbLoading.value = true
  try {
    const res = await listKnowledgeBase()
    const data = res?.data
    const rows = Array.isArray(data) ? data : Array.isArray(data?.rows) ? data.rows : []
    kbOptions.value = rows.map(kb => ({
      kb_id: kb?.kb_id ?? kb?.kbId,
      kb_name: kb?.kb_name ?? kb?.kbName ?? String(kb?.kb_id ?? '')
    }))
    kbLoaded.value = true
  } catch (e) {
    kbOptions.value = []
    kbLoaded.value = false
    ElMessage.error(e?.message || '获取知识库列表失败')
  } finally {
    kbLoading.value = false
  }
}

async function handleKbVisibleChange(v) {
  if (v && !kbLoaded.value) {
    await loadKbOptions()
  }
}

async function loadModelOptions() {
  if (modelLoading.value) return
  modelLoading.value = true
  try {
    const res = await listModelAll()
    const data = res?.data
    const rows = Array.isArray(data) ? data : Array.isArray(data?.rows) ? data.rows : []
    modelOptions.value = rows.map(m => ({
      model_id: m.model_id ?? m.modelId,
      model_name: m.model_name ?? m.modelName ?? String(m.model_id ?? '')
    }))
    modelLoaded.value = true
  } catch (e) {
    modelOptions.value = []
  } finally {
    modelLoading.value = false
  }
}

async function handleModelVisibleChange(v) {
  if (v && !modelLoaded.value) {
    await loadModelOptions()
  }
}

async function submitSelf() {
  const name = selfTaskName.value.trim()
  if (!name) {
    ElMessage.warning('请输入课题名称')
    return
  }
  const desc = selfTaskDescription.value.trim()
  creating.value = true
  try {
    selfDialogVisible.value = false
    selfTaskName.value = ''
    selfTaskDescription.value = ''
    await createStudentTask({
      task_name: name,
      task_description: desc || undefined,
      scenario_kb_ids: selfScenarioKbIds.value,
      decision_kb_ids: selfDecisionKbIds.value,
      reflection_kb_ids: selfReflectionKbIds.value,
      research_kb_ids: selfResearchKbIds.value,
      review_model_id: selfReviewModelId.value || undefined,
    })
    ElMessage.success('创建成功')
    getList()
  } finally {
    creating.value = false
  }
}

function openSelfDialog() {
  selfTaskName.value = ''
  selfTaskDescription.value = ''
  // 默认选中公用知识库
  selfScenarioKbIds.value = [DEFAULT_KB_ID]
  selfDecisionKbIds.value = [DEFAULT_KB_ID]
  selfReflectionKbIds.value = [DEFAULT_KB_ID]
  selfResearchKbIds.value = [DEFAULT_KB_ID]
  selfReviewModelId.value = undefined
  selfDialogVisible.value = true
  // 预加载知识库列表
  if (!kbLoaded.value) {
    loadKbOptions()
  }
}

async function openDetail(row) {
  const res = await getTaskDetail(row.task_id)
  detail.value = normalizeTaskRow(res.data || {})
  detailVisible.value = true
}

onMounted(() => {
  loadDeptOptions()
  getList()
})
</script>

<style scoped>
.mr4 { margin-right: 4px; }
.class-cell {
  display: inline-block;
  max-width: 100%;
  cursor: pointer;
  color: var(--el-color-primary);
}
.class-ellipsis {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
</style>
