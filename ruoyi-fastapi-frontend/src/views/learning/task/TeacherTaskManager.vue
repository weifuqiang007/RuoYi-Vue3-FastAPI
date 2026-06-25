<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="任务名称" prop="task_name">
        <el-input
          v-model="queryParams.task_name"
          placeholder="请输入任务名称"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="学生姓名" prop="student_name">
        <el-input
          v-model="queryParams.student_name"
          placeholder="自研课题创建者"
          clearable
          style="width: 180px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="归属班级" prop="dept_id">
        <el-select v-model="queryParams.dept_id" placeholder="请选择班级" clearable filterable style="width: 200px">
          <el-option v-for="d in deptOptions" :key="d.deptId" :label="d.deptName" :value="d.deptId" />
        </el-select>
      </el-form-item>
      <el-form-item label="类型" prop="creator_type">
        <el-select v-model="queryParams.creator_type" placeholder="全部" clearable style="width: 140px">
          <el-option label="教学任务" value="0" />
          <el-option label="自研课题" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item label="发布教师" prop="teacher_name">
        <el-input
          v-model="queryParams.teacher_name"
          placeholder="请输入教师姓名"
          clearable
          style="width: 160px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="任务简述" prop="task_description">
        <el-input
          v-model="queryParams.task_description"
          placeholder="请输入任务简述"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="发布时间">
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
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="全部" clearable style="width: 140px">
          <el-option label="草稿" value="0" />
          <el-option label="已发布" value="1" />
          <el-option label="已关闭" value="2" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd">创建任务</el-button>
      </el-col>
    </el-row>

    <el-table v-loading="loading" :data="taskList">
      <el-table-column label="类型" width="100" align="center">
        <template #default="scope">
          <el-tag v-if="String(scope.row.creator_type) === '1'" type="success">自研课题</el-tag>
          <el-tag v-else type="primary">教学任务</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="任务名称" prop="task_name" min-width="180" show-overflow-tooltip />
      <el-table-column label="归属班级" min-width="200">
        <template #default="scope">
          <span v-if="String(scope.row.creator_type) === '1'" style="color: #909399;">-</span>
          <span
            v-else-if="scope.row.assigned_classes && scope.row.assigned_classes.length > 0"
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
      <el-table-column label="创建者" width="110" align="center">
        <template #default="scope">
          <span v-if="String(scope.row.creator_type) === '1'">{{ scope.row.student_name || '-' }}</span>
          <span v-else>{{ scope.row.teacher_name || '我' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="scope">
          <el-tag :type="statusTagType(scope.row.status)">
            {{ statusLabel(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="任务简述" prop="task_description" min-width="220" show-overflow-tooltip />
      <el-table-column label="分配班级" min-width="160" show-overflow-tooltip>
        <template #default="scope">
          <template v-if="scope.row.creator_type === '1'">
            <span style="color: #909399;">-</span>
          </template>
          <template v-else-if="scope.row.assigned_classes && scope.row.assigned_classes.length > 0">
            <el-tag v-for="c in scope.row.assigned_classes" :key="c.dept_id" size="small" class="mr4">
              {{ c.dept_name }}
            </el-tag>
          </template>
          <template v-else>
            <span style="color: #e6a23c;">未分配</span>
          </template>
        </template>
      </el-table-column>
      <el-table-column label="截止时间" prop="deadline" width="170" />
      <el-table-column label="创建时间" prop="create_time" width="170" />
      <el-table-column label="操作" width="260" align="center">
        <template #default="scope">
          <el-button
            v-if="String(scope.row.creator_type) !== '1'"
            link
            type="primary"
            icon="Edit"
            @click="handleEdit(scope.row)"
          >
            编辑
          </el-button>
          <el-button
            v-if="String(scope.row.creator_type) !== '1'"
            link
            type="danger"
            icon="Delete"
            @click="handleDelete(scope.row)"
          >
            删除
          </el-button>
          <el-button v-if="String(scope.row.creator_type) === '1'" link type="info" icon="View" @click="handleMore('detail', scope.row)">
            详情
          </el-button>
          <el-dropdown @command="(cmd) => handleMore(cmd, scope.row)">
            <span class="el-dropdown-link">
              更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="String(scope.row.creator_type) !== '1'" command="publish">发布到班级</el-dropdown-item>
                <el-dropdown-item command="detail">查看详情</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
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

    <TaskFormDialog v-model="dialogVisible" :data="editingRow" @success="handleDialogSuccess" />

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

    <el-dialog title="发布到班级" v-model="publishVisible" width="520px">
      <el-form label-width="90px">
        <el-form-item label="选择班级" required>
          <el-select v-model="publishDeptIds" multiple filterable style="width: 100%">
            <el-option v-for="d in deptOptions" :key="d.deptId" :label="d.deptName" :value="d.deptId" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="publishVisible = false">取 消</el-button>
        <el-button type="primary" :loading="publishing" @click="submitPublish">确 定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="任务详情" size="40%">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="任务名称">{{ detail.task_name }}</el-descriptions-item>
        <el-descriptions-item label="任务描述">{{ detail.task_description }}</el-descriptions-item>
        <el-descriptions-item label="预设情境">{{ detail.preset_scenario }}</el-descriptions-item>
        <el-descriptions-item label="情境区KB">{{ formatKbIds(detail.scenario_kb_ids) }}</el-descriptions-item>
        <el-descriptions-item label="决策区KB">{{ formatKbIds(detail.decision_kb_ids) }}</el-descriptions-item>
        <el-descriptions-item label="反思区KB">{{ formatKbIds(detail.reflection_kb_ids) }}</el-descriptions-item>
        <el-descriptions-item label="研究区KB">{{ formatKbIds(detail.research_kb_ids) }}</el-descriptions-item>
        <el-descriptions-item label="截止时间">{{ detail.deadline }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup name="TeacherTaskManager">
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listTeacherTask, createTask, updateTask, deleteTask, publishTask, getTaskDetail } from '@/api/learning/task'
import { listDept } from '@/api/system/dept'
import { listKnowledgeBase } from '@/api/rag/knowledgeBase'
import TaskFormDialog from './components/TaskFormDialog.vue'

const { proxy } = getCurrentInstance()

const loading = ref(false)
const showSearch = ref(true)
const taskList = ref([])
const total = ref(0)
const deadlineRange = ref([])
const createTimeRange = ref([])

const queryParams = ref({
  page_num: 1,
  page_size: 10,
  creator_type: undefined,
  task_name: undefined,
  dept_id: undefined,
  teacher_name: undefined,
  student_name: undefined,
  task_description: undefined,
  status: undefined
})

const queryRef = ref()

const dialogVisible = ref(false)
const editingRow = ref({})

const publishVisible = ref(false)
const publishing = ref(false)
const publishDeptIds = ref([])
const deptOptions = ref([])
const publishTaskId = ref(null)

const detailVisible = ref(false)
const detail = ref({})
const kbOptions = ref([])
const kbLoading = ref(false)
const kbLoaded = ref(false)

const kbNameMap = computed(() => {
  return new Map(kbOptions.value.map(kb => [String(kb.kb_id), kb.kb_name]))
})

const assignedClassVisible = ref(false)
const assignedClassList = ref([])

function normalizeTaskRow(row) {
  return {
    task_id: row.task_id ?? row.taskId,
    task_name: row.task_name ?? row.taskName,
    task_description: row.task_description ?? row.taskDescription,
    preset_scenario: row.preset_scenario ?? row.presetScenario,
    scenario_kb_ids: normalizeKbIdList(row.scenario_kb_ids ?? row.scenarioKbIds),
    decision_kb_ids: normalizeKbIdList(row.decision_kb_ids ?? row.decisionKbIds),
    reflection_kb_ids: normalizeKbIdList(row.reflection_kb_ids ?? row.reflectionKbIds),
    research_kb_ids: normalizeKbIdList(row.research_kb_ids ?? row.researchKbIds),
    deadline: row.deadline,
    status: row.status,
    create_time: row.create_time ?? row.createTime,
    creator_type: row.creator_type ?? row.creatorType,
    student_id: row.student_id ?? row.studentId,
    student_name: row.student_name ?? row.studentName,
    teacher_id: row.teacher_id ?? row.teacherId,
    teacher_name: row.teacher_name ?? row.teacherName,
    assigned_classes: row.assigned_classes ?? row.assignedClasses ?? []
  }
}

function normalizeKbId(id) {
  if (id === null || id === undefined || id === '') return id
  const n = Number(id)
  return Number.isNaN(n) ? id : n
}

function normalizeKbIdList(value) {
  if (Array.isArray(value)) return value.map(normalizeKbId).filter(id => id !== null && id !== undefined && id !== '')
  if (typeof value === 'string') {
    const text = value.trim()
    if (!text) return []
    try {
      const parsed = JSON.parse(text)
      if (Array.isArray(parsed)) return normalizeKbIdList(parsed)
    } catch (e) {
      // Ignore non-JSON strings and fall back to comma separated ids.
    }
    return text.split(',').map(item => normalizeKbId(item.trim())).filter(id => id !== null && id !== undefined && id !== '')
  }
  return value === null || value === undefined ? [] : [normalizeKbId(value)]
}

function normalizeKbOption(kb) {
  const rawId = kb?.kb_id ?? kb?.kbId
  return {
    ...kb,
    kb_id: normalizeKbId(rawId),
    kb_name: kb?.kb_name ?? kb?.kbName ?? String(rawId ?? '')
  }
}

async function loadKbOptions() {
  if (kbLoading.value) return
  kbLoading.value = true
  try {
    const res = await listKnowledgeBase()
    const data = res?.data
    const rows = Array.isArray(data) ? data : Array.isArray(data?.rows) ? data.rows : []
    kbOptions.value = rows.map(normalizeKbOption)
    kbLoaded.value = true
  } catch (e) {
    kbOptions.value = []
    kbLoaded.value = false
    ElMessage.error(e?.message || '获取知识库列表失败')
  } finally {
    kbLoading.value = false
  }
}

async function ensureKbOptions() {
  if (kbLoaded.value && kbOptions.value.length > 0) return
  await loadKbOptions()
}

function statusLabel(v) {
  const key = String(v ?? '')
  return { '0': '草稿', '1': '已发布', '2': '已关闭' }[key] || '未知'
}

function statusTagType(v) {
  const key = String(v ?? '')
  return { '0': 'info', '1': 'success', '2': 'warning' }[key] || 'info'
}

async function getDeptOptions() {
  const res = await listDept()
  const data = res?.data
  deptOptions.value = Array.isArray(data) ? data : Array.isArray(data?.rows) ? data.rows : []
}

function buildQueryParams() {
  const q = queryParams.value
  const params = {
    page_num: q.page_num,
    page_size: q.page_size
  }
  if (q.creator_type) params.creator_type = q.creator_type
  if (q.task_name) params.task_name = q.task_name
  if (q.teacher_name) params.teacher_name = q.teacher_name
  if (q.student_name) params.student_name = q.student_name
  if (q.task_description) params.task_description = q.task_description
  if (q.status) params.status = q.status
  if (q.dept_id !== undefined && q.dept_id !== null && q.dept_id !== '') {
    params.dept_id = q.dept_id
  }
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
  listTeacherTask(buildQueryParams())
    .then(res => {
      const data = res?.data ?? {}
      const rows = Array.isArray(data.rows) ? data.rows : Array.isArray(res?.rows) ? res.rows : []
      const totalVal = data.total ?? res?.total ?? 0
      taskList.value = rows.map(normalizeTaskRow)
      total.value = totalVal
    })
    .finally(() => {
      loading.value = false
    })
}

function handleQuery() {
  queryParams.value.page_num = 1
  getList()
}

function resetQuery() {
  deadlineRange.value = []
  createTimeRange.value = []
  queryRef.value?.resetFields?.()
  queryParams.value.page_num = 1
  queryParams.value.page_size = 10
  getList()
}

function handleAdd() {
  editingRow.value = {}
  dialogVisible.value = true
}

async function handleEdit(row) {
  try {
    await ensureKbOptions()
    const res = await getTaskDetail(row.task_id)
    editingRow.value = normalizeTaskRow(res.data || row)
    dialogVisible.value = true
  } catch (e) {
    ElMessage.error(e?.message || '获取任务详情失败')
  }
}

async function handleDialogSuccess(payload) {
  if (payload.task_id) {
    await updateTask(payload)
    ElMessage.success('更新成功')
  } else {
    await createTask(payload)
    ElMessage.success('创建成功')
  }
  getList()
}

function handleDelete(row) {
  proxy.$modal
    .confirm(`确认删除任务「${row.task_name}」？`)
    .then(() => deleteTask(row.task_id))
    .then(() => {
      proxy.$modal.msgSuccess('删除成功')
      getList()
    })
    .catch(() => {})
}

async function handleMore(cmd, row) {
  if (cmd === 'publish') {
    if (String(row.creator_type) === '1') return
    publishTaskId.value = row.task_id
    publishDeptIds.value = []
    if (deptOptions.value.length === 0) {
      await getDeptOptions()
    }
    publishVisible.value = true
    return
  }
  if (cmd === 'detail') {
    try {
      await ensureKbOptions()
      const res = await getTaskDetail(row.task_id)
      detail.value = normalizeTaskRow(res.data || row)
      detailVisible.value = true
    } catch (e) {
      ElMessage.error(e?.message || '获取任务详情失败')
    }
  }
}

async function submitPublish() {
  if (!publishTaskId.value) return
  if (publishDeptIds.value.length === 0) {
    ElMessage.warning('请至少选择一个班级')
    return
  }
  publishing.value = true
  try {
    await publishTask(publishTaskId.value, { dept_ids: publishDeptIds.value })
    ElMessage.success('发布成功')
    publishVisible.value = false
    getList()
  } finally {
    publishing.value = false
  }
}

function formatKbIds(v) {
  const ids = normalizeKbIdList(v)
  if (ids.length === 0) return '-'
  return ids.map(id => kbNameMap.value.get(String(id)) || `知识库#${id}`).join('、')
}

function formatAssignedClasses(list) {
  if (!Array.isArray(list) || list.length === 0) return ''
  return list.map(c => c.dept_name ?? c.deptName ?? '').filter(Boolean).join('、')
}

function openAssignedClassDialog(row) {
  assignedClassList.value = Array.isArray(row?.assigned_classes) ? row.assigned_classes : []
  assignedClassVisible.value = true
}

onMounted(() => {
  getDeptOptions()
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
