<template>
  <div class="app-container">
    <el-form ref="queryRef" :model="queryParams" :inline="true" class="mb8">
      <el-form-item label="课题类型">
        <el-select v-model="queryParams.creator_type" placeholder="全部" clearable style="width: 160px">
          <el-option label="教学任务" value="0" />
          <el-option label="自研课题" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item label="课题名称">
        <el-input
          v-model="queryParams.task_name"
          placeholder="请输入课题名称"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="创建时间">
        <el-date-picker
          v-model="createTimeRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 260px"
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
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="recordList">
      <el-table-column label="记录ID" prop="record_id" width="90" />
      <el-table-column label="课题名称" width="140" show-overflow-tooltip>
        <template #default="scope">
          <el-button link type="primary" @click="enter(scope.row)">
            {{ scope.row.task_name || '-' }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="课题描述" prop="task_description" min-width="200" show-overflow-tooltip />
      <el-table-column label="创建者" prop="creator_name" width="120" show-overflow-tooltip />
      <el-table-column label="课题类型" width="110" align="center">
        <template #default="scope">
          <el-tag v-if="String(scope.row.creator_type) === '1'" type="success">自研课题</el-tag>
          <el-tag v-else type="primary">教学任务</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="截止时间" prop="deadline" width="170" />
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
      v-model:page="queryParams.page_num"
      v-model:limit="queryParams.page_size"
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

const queryRef = ref()
const createTimeRange = ref([])
const deadlineRange = ref([])
const queryParams = reactive({
  page_num: 1,
  page_size: 10,
  creator_type: undefined,
  task_name: undefined
})

function normalizeRow(row) {
  return {
    record_id: row.record_id ?? row.recordId,
    task_name: row.task_name ?? row.taskName ?? (row.task_id ? `任务#${row.task_id}` : ''),
    task_description: row.task_description ?? row.taskDescription,
    creator_type: row.creator_type ?? row.creatorType,
    creator_name: row.creator_name ?? row.creatorName,
    deadline: row.deadline,
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

function buildQueryParams() {
  const params = {
    page_num: queryParams.page_num,
    page_size: queryParams.page_size
  }
  if (queryParams.creator_type) params.creator_type = queryParams.creator_type
  if (queryParams.task_name) params.task_name = queryParams.task_name
  if (Array.isArray(createTimeRange.value) && createTimeRange.value.length === 2) {
    params.create_time_begin = createTimeRange.value[0]
    params.create_time_end = createTimeRange.value[1]
  }
  if (Array.isArray(deadlineRange.value) && deadlineRange.value.length === 2) {
    params.deadline_begin = deadlineRange.value[0]
    params.deadline_end = deadlineRange.value[1]
  }
  return params
}

function getList() {
  loading.value = true
  listMyRecord(buildQueryParams())
    .then(res => {
      const data = res?.data ?? {}
      const rows = Array.isArray(data.rows) ? data.rows : Array.isArray(res?.rows) ? res.rows : []
      recordList.value = rows
        .map(normalizeRow)
        .sort((a, b) => Number(a.record_id ?? 0) - Number(b.record_id ?? 0))
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
  createTimeRange.value = []
  deadlineRange.value = []
  queryRef.value?.resetFields?.()
  queryParams.page_num = 1
  queryParams.page_size = 10
  getList()
}

function enter(row) {
  router.push({ path: '/learning/zone', query: { record_id: row.record_id } })
}

onMounted(() => {
  getList()
})
</script>
