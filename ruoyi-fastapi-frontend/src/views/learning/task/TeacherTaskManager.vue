<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="任务名称" prop="taskName">
        <el-input
          v-model="queryParams.taskName"
          placeholder="请输入任务名称"
          clearable
          style="width: 220px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="类型">
        <el-select v-model="creatorTypeFilter" placeholder="全部" clearable style="width: 160px">
          <el-option label="教学任务" value="0" />
          <el-option label="自研课题" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="状态" clearable style="width: 160px">
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

    <el-table v-loading="loading" :data="displayTaskList">
      <el-table-column label="类型" width="100" align="center">
        <template #default="scope">
          <el-tag v-if="String(scope.row.creator_type) === '1'" type="success">自研课题</el-tag>
          <el-tag v-else type="primary">教学任务</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="任务名称" prop="task_name" min-width="180" show-overflow-tooltip />
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
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <TaskFormDialog v-model="dialogVisible" :data="editingRow" @success="handleDialogSuccess" />

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
import TaskFormDialog from './components/TaskFormDialog.vue'

const { proxy } = getCurrentInstance()

const loading = ref(false)
const showSearch = ref(true)
const taskList = ref([])
const total = ref(0)
const creatorTypeFilter = ref(undefined)

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  taskName: undefined,
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

function normalizeTaskRow(row) {
  return {
    task_id: row.task_id ?? row.taskId,
    task_name: row.task_name ?? row.taskName,
    task_description: row.task_description ?? row.taskDescription,
    preset_scenario: row.preset_scenario ?? row.presetScenario,
    scenario_kb_ids: row.scenario_kb_ids ?? row.scenarioKbIds ?? [],
    decision_kb_ids: row.decision_kb_ids ?? row.decisionKbIds ?? [],
    reflection_kb_ids: row.reflection_kb_ids ?? row.reflectionKbIds ?? [],
    research_kb_ids: row.research_kb_ids ?? row.researchKbIds ?? [],
    deadline: row.deadline,
    status: row.status,
    create_time: row.create_time ?? row.createTime,
    creator_type: row.creator_type ?? row.creatorType,
    student_id: row.student_id ?? row.studentId,
    student_name: row.student_name ?? row.studentName,
    teacher_id: row.teacher_id ?? row.teacherId,
    teacher_name: row.teacher_name ?? row.teacherName,
    assigned_classes: row.assigned_classes ?? []
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

async function getDeptOptions() {
  const res = await listDept()
  deptOptions.value = res.data || []
}

function getList() {
  loading.value = true
  listTeacherTask(queryParams.value)
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

const displayTaskList = computed(() => {
  const filter = creatorTypeFilter.value
  if (!filter) return taskList.value
  return taskList.value.filter(item => String(item.creator_type) === String(filter))
})

function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

function resetQuery() {
  queryParams.value.taskName = undefined
  queryParams.value.status = undefined
  creatorTypeFilter.value = undefined
  queryRef.value?.resetFields?.()
  handleQuery()
}

function handleAdd() {
  editingRow.value = {}
  dialogVisible.value = true
}

function handleEdit(row) {
  editingRow.value = { ...row }
  dialogVisible.value = true
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
    const res = await getTaskDetail(row.task_id)
    detail.value = normalizeTaskRow(res.data || {})
    detailVisible.value = true
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
  if (!v) return ''
  if (Array.isArray(v)) return v.join(', ')
  return String(v)
}

onMounted(() => {
  getList()
})
</script>

<style scoped>
.mr4 { margin-right: 4px; }
</style>
