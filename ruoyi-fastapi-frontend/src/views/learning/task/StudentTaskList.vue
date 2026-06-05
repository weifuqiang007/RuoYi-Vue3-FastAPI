<template>
  <div class="app-container">
    <el-alert
      title="这里展示教师发布到你班级的任务。你也可以创建「自研课题」进入四区流程。"
      type="info"
      :closable="false"
      show-icon
      class="mb8"
    />

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="openSelfDialog">新增自研课题</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button icon="Refresh" @click="getList">刷新</el-button>
      </el-col>
    </el-row>

    <el-table v-loading="loading" :data="taskList">
      <el-table-column label="任务名称" prop="task_name" min-width="200" show-overflow-tooltip />
      <el-table-column label="截止时间" prop="deadline" width="170" />
      <el-table-column label="状态" width="90" align="center">
        <template #default="scope">
          <el-tag type="success">已发布</el-tag>
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
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <el-dialog title="新增自研课题" v-model="selfDialogVisible" width="520px">
      <el-form label-width="90px">
        <el-form-item label="课题名称" required>
          <el-input v-model="selfTaskName" placeholder="请输入课题名称" />
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
  </div>
</template>

<script setup name="StudentTaskList">
import { ElMessage } from 'element-plus'
import { listStudentTask, getTaskDetail } from '@/api/learning/task'
import { startRecord, createSelfRecord } from '@/api/learning/record'

const router = useRouter()

const loading = ref(false)
const taskList = ref([])
const total = ref(0)
const queryParams = ref({
  pageNum: 1,
  pageSize: 10
})

const selfDialogVisible = ref(false)
const selfTaskName = ref('')
const creating = ref(false)

const detailVisible = ref(false)
const detail = ref({})

function normalizeTaskRow(row) {
  return {
    task_id: row.task_id ?? row.taskId,
    task_name: row.task_name ?? row.taskName,
    task_description: row.task_description ?? row.taskDescription,
    preset_scenario: row.preset_scenario ?? row.presetScenario,
    deadline: row.deadline
  }
}

function getList() {
  loading.value = true
  listStudentTask(queryParams.value)
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

async function handleStart(row) {
  const res = await startRecord(row.task_id)
  const recordId = res?.data?.record_id ?? res?.data?.recordId ?? res?.data?.record_id ?? res?.data
  if (!recordId) {
    ElMessage.success('已开始任务')
    return
  }
  await router.push({ path: '/learning/zone', query: { record_id: recordId } })
}

async function submitSelf() {
  const name = selfTaskName.value.trim()
  if (!name) {
    ElMessage.warning('请输入课题名称')
    return
  }
  creating.value = true
  try {
    const res = await createSelfRecord({ task_name: name })
    const recordId = res?.data?.record_id ?? res?.data?.recordId ?? res?.data
    selfDialogVisible.value = false
    selfTaskName.value = ''
    if (recordId) {
      await router.push({ path: '/learning/zone', query: { record_id: recordId } })
    } else {
      ElMessage.success('创建成功')
    }
  } finally {
    creating.value = false
  }
}

function openSelfDialog() {
  selfTaskName.value = ''
  selfDialogVisible.value = true
}

async function openDetail(row) {
  const res = await getTaskDetail(row.task_id)
  detail.value = normalizeTaskRow(res.data || {})
  detailVisible.value = true
}

onMounted(() => {
  getList()
})
</script>
