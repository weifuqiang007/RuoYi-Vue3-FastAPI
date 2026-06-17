<template>
  <div class="app-container">
    <el-alert
      title="按班级/任务/学生筛选，查看学生提交的反思性研究成果。AI（裁判模型）先评论，老师再针对学生结论点评。"
      type="info"
      :closable="false"
      show-icon
      class="mb8"
    />

    <el-form ref="queryRef" :model="queryParams" :inline="true" class="mb8">
      <el-form-item label="课题类型">
        <el-select v-model="queryParams.creator_type" placeholder="全部" clearable style="width: 140px">
          <el-option label="教学任务" value="0" />
          <el-option label="自研课题" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item label="班级">
        <el-select v-model="queryParams.class_id" placeholder="全部" clearable filterable style="width: 200px">
          <el-option v-for="d in deptOptions" :key="d.deptId" :label="d.deptName" :value="d.deptId" />
        </el-select>
      </el-form-item>
      <el-form-item label="学生姓名">
        <el-input
          v-model="queryParams.student_name"
          placeholder="模糊匹配"
          clearable
          style="width: 160px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="批阅状态">
        <el-select v-model="queryParams.review_status" placeholder="全部" clearable style="width: 160px">
          <el-option label="待批阅" value="pending" />
          <el-option label="已点评" value="commented" />
          <el-option label="未生成AI评论" value="no_ai" />
        </el-select>
      </el-form-item>
      <el-form-item label="提交时间">
        <el-date-picker
          v-model="submitRange"
          type="daterange"
          value-format="YYYY-MM-DD HH:mm:ss"
          range-separator="-"
          start-placeholder="开始"
          end-placeholder="结束"
          style="width: 340px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="list">
      <el-table-column label="学生" prop="student_name" width="110" />
      <el-table-column label="课题" prop="task_name" min-width="200" show-overflow-tooltip />
      <el-table-column label="类型" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="String(row.creator_type) === '1'" type="success">自研</el-tag>
          <el-tag v-else type="primary">教学</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="班级" prop="class_name" width="140" show-overflow-tooltip />
      <el-table-column label="提交时间" prop="submit_time" width="170" />
      <el-table-column label="AI评论" width="110" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.ai_commented" type="success">v{{ row.ai_comment_version }}</el-tag>
          <el-tag v-else type="info">未生成</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="点评" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.review_status === '1'" type="success">已点评</el-tag>
          <el-tag v-else-if="row.review_status === '0'" type="warning">草稿</el-tag>
          <el-tag v-else type="info">未点评</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="110" align="center">
        <template #default="{ row }">
          <el-button type="primary" link icon="Edit" @click="openReview(row)">批阅</el-button>
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

    <ReviewDrawer v-model="drawerVisible" :record-id="drawerRecordId" />
  </div>
</template>

<script setup name="ReviewIndex">
import { ElMessage } from 'element-plus'
import { listReviewRecords } from '@/api/learning/review'
import { listDept } from '@/api/system/dept'
import ReviewDrawer from './components/ReviewDrawer.vue'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const queryRef = ref()
const deptOptions = ref([])
const submitRange = ref([])
const drawerVisible = ref(false)
const drawerRecordId = ref(null)

const queryParams = reactive({
  page_num: 1,
  page_size: 10,
  creator_type: undefined,
  class_id: undefined,
  student_name: undefined,
  review_status: undefined
})

function buildParams() {
  const p = { page_num: queryParams.page_num, page_size: queryParams.page_size }
  if (queryParams.creator_type) p.creator_type = queryParams.creator_type
  if (queryParams.class_id !== undefined && queryParams.class_id !== null && queryParams.class_id !== '') {
    p.class_id = queryParams.class_id
  }
  if (queryParams.student_name) p.student_name = queryParams.student_name
  if (queryParams.review_status) p.review_status = queryParams.review_status
  if (Array.isArray(submitRange.value) && submitRange.value.length === 2) {
    p.submit_time_begin = submitRange.value[0]
    p.submit_time_end = submitRange.value[1]
  }
  return p
}

function getList() {
  loading.value = true
  listReviewRecords(buildParams())
    .then(res => {
      const data = res?.data ?? {}
      list.value = Array.isArray(data.rows) ? data.rows : []
      total.value = data.total ?? 0
    })
    .catch(() => {
      list.value = []
      total.value = 0
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
  queryRef.value?.resetFields?.()
  submitRange.value = []
  queryParams.page_num = 1
  getList()
}

function openReview(row) {
  drawerRecordId.value = row.record_id
  drawerVisible.value = true
}

async function loadDept() {
  try {
    const res = await listDept()
    const data = res?.data
    deptOptions.value = Array.isArray(data) ? data : Array.isArray(data?.rows) ? data.rows : []
  } catch (e) {
    deptOptions.value = []
  }
}

onMounted(() => {
  loadDept()
  getList()
})
</script>

<style scoped>
.mb8 {
  margin-bottom: 12px;
}
</style>
