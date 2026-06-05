<template>
  <div class="app-container">
    <el-table v-loading="loading" :data="recordList">
      <el-table-column label="记录ID" prop="record_id" width="90" />
      <el-table-column label="课题/任务" prop="task_name" min-width="220" show-overflow-tooltip />
      <el-table-column label="当前阶段" width="110" align="center">
        <template #default="scope">
          <el-tag :type="stageTagType(scope.row.current_stage)">{{ stageLabel(scope.row.current_stage) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="开始时间" prop="start_time" width="170" />
      <el-table-column label="操作" width="140" align="center">
        <template #default="scope">
          <el-button type="primary" link icon="Position" @click="enter(scope.row)">进入</el-button>
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
  </div>
</template>

<script setup name="MyRecordList">
import { listMyRecord } from '@/api/learning/record'

const router = useRouter()

const loading = ref(false)
const recordList = ref([])
const total = ref(0)

const queryParams = ref({
  pageNum: 1,
  pageSize: 10
})

function normalizeRow(row) {
  return {
    record_id: row.record_id ?? row.recordId,
    task_id: row.task_id ?? row.taskId,
    task_name: row.task_name ?? row.taskName ?? (row.task_id ? `任务#${row.task_id}` : '自研课题'),
    current_stage: row.current_stage ?? row.currentStage ?? 'scenario',
    start_time: row.start_time ?? row.startTime
  }
}

function stageLabel(stage) {
  const key = String(stage || '')
  return { scenario: '情境', decision: '决策', reflection: '反思', research: '研究', submitted: '已提交', completed: '已完成' }[key] || key
}

function stageTagType(stage) {
  const key = String(stage || '')
  return { scenario: 'info', decision: 'warning', reflection: 'primary', research: 'success', submitted: 'success', completed: 'success' }[key] || 'info'
}

function getList() {
  loading.value = true
  listMyRecord(queryParams.value)
    .then(res => {
      const data = res?.data ?? {}
      const rows = Array.isArray(data.rows) ? data.rows : Array.isArray(res?.rows) ? res.rows : []
      recordList.value = rows.map(normalizeRow)
      total.value = data.total ?? res?.total ?? 0
    })
    .finally(() => {
      loading.value = false
    })
}

function enter(row) {
  router.push({ path: '/learning/zone', query: { record_id: row.record_id } })
}

onMounted(() => {
  getList()
})
</script>

