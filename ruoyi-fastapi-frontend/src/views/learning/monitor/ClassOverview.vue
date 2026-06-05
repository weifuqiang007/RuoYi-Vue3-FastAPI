<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="选择任务" prop="taskId">
        <el-select v-model="queryParams.taskId" placeholder="请选择教学任务" clearable style="width: 300px" @change="handleQuery">
          <el-option v-for="t in taskOptions" :key="t.task_id" :label="t.task_name" :value="t.task_id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">查询</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="mb8" v-if="overview.total_students > 0">
      <el-col :span="4">
        <el-statistic title="总学生数" :value="overview.total_students" />
      </el-col>
      <el-col :span="4">
        <el-statistic title="情境区">
          :value="stageCount('scenario')" />
      </el-col>
      <el-col :span="4">
        <el-statistic title="决策区" :value="stageCount('decision')" />
      </el-col>
      <el-col :span="4">
        <el-statistic title="反思区" :value="stageCount('reflection')" />
      </el-col>
      <el-col :span="4">
        <el-statistic title="研究区" :value="stageCount('research')" />
      </el-col>
      <el-col :span="4">
        <el-statistic title="已提交" :value="stageCount('submitted') + stageCount('completed')" />
      </el-col>
    </el-row>

    <el-divider />

    <!-- 学生列表 -->
    <el-table v-loading="loading" :data="studentList">
      <el-table-column label="学生ID" prop="student_id" width="90" />
      <el-table-column label="当前阶段" width="110" align="center">
        <template #default="scope">
          <el-tag :type="stageTagType(scope.row.current_stage)">{{ stageLabel(scope.row.current_stage) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="情境" width="70" align="center">
        <template #default="scope">
          <el-icon :color="scope.row.scenario_status === '2' ? '#67C23A' : '#909399'">
            <component :is="scope.row.scenario_status === '2' ? 'CircleCheck' : 'Clock'" />
          </el-icon>
        </template>
      </el-table-column>
      <el-table-column label="决策" width="70" align="center">
        <template #default="scope">
          <el-icon :color="scope.row.decision_status === '2' ? '#67C23A' : '#909399'">
            <component :is="scope.row.decision_status === '2' ? 'CircleCheck' : 'Clock'" />
          </el-icon>
        </template>
      </el-table-column>
      <el-table-column label="反思" width="70" align="center">
        <template #default="scope">
          <el-icon :color="scope.row.reflection_status === '2' ? '#67C23A' : '#909399'">
            <component :is="scope.row.reflection_status === '2' ? 'CircleCheck' : 'Clock'" />
          </el-icon>
        </template>
      </el-table-column>
      <el-table-column label="研究" width="70" align="center">
        <template #default="scope">
          <el-icon :color="scope.row.research_status === '2' ? '#67C23A' : '#909399'">
            <component :is="scope.row.research_status === '2' ? 'CircleCheck' : 'Clock'" />
          </el-icon>
        </template>
      </el-table-column>
      <el-table-column label="提交时间" prop="submit_time" width="170" />
      <el-table-column label="操作" width="140" align="center">
        <template #default="scope">
          <el-button type="primary" link icon="View" @click="viewDetail(scope.row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 学生详情抽屉 -->
    <el-drawer v-model="detailVisible" title="学生学习详情" size="55%">
      <div v-if="studentDetail.record_id">
        <el-descriptions :column="2" border class="mb8">
          <el-descriptions-item label="当前阶段">
            <el-tag :type="stageTagType(studentDetail.current_stage)">{{ stageLabel(studentDetail.current_stage) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">{{ studentDetail.status }}</el-descriptions-item>
        </el-descriptions>

        <!-- 情境区 -->
        <el-card class="box-card mb8" v-if="studentDetail.scenario">
          <template #header><span class="card-header">情境区</span></template>
          <p>{{ studentDetail.scenario.description }}</p>
          <div v-if="studentDetail.scenario.key_events" class="mt8">
            <strong>关键事件：</strong>
            <el-tag v-for="(e, i) in studentDetail.scenario.key_events" :key="i" class="mr4" size="small">{{ e.event }}</el-tag>
          </div>
        </el-card>

        <!-- 决策区 -->
        <el-card class="box-card mb8" v-if="studentDetail.decisions && studentDetail.decisions.length">
          <template #header><span class="card-header">决策区 ({{ studentDetail.decisions.length }}条)</span></template>
          <div v-for="(d, i) in studentDetail.decisions" :key="i" class="mb8">
            <p><strong>节点：</strong>{{ d.key_event_desc }}</p>
            <p><strong>行动：</strong>{{ d.action_taken }}</p>
            <p><strong>理由：</strong>{{ d.reasoning }}</p>
            <el-divider v-if="i < studentDetail.decisions.length - 1" />
          </div>
        </el-card>

        <!-- 反思区 -->
        <el-card class="box-card mb8" v-if="studentDetail.reflection">
          <template #header><span class="card-header">反思区</span></template>
          <p>深度: <el-tag size="small">{{ studentDetail.reflection.depth_level }}</el-tag> ({{ studentDetail.reflection.depth_score }})</p>
          <p class="mt8">{{ studentDetail.reflection.content }}</p>
        </el-card>

        <!-- 研究区 -->
        <el-card class="box-card mb8" v-if="studentDetail.research">
          <template #header><span class="card-header">研究生成区</span></template>
          <p><strong>研究问题：</strong>{{ studentDetail.research.selected_question }}</p>
        </el-card>

        <!-- 评价区 -->
        <el-card class="box-card mb8" v-if="studentDetail.evaluation">
          <template #header><span class="card-header">教师评价</span></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="总分">{{ studentDetail.evaluation.total_score }}</el-descriptions-item>
            <el-descriptions-item label="优秀">{{ studentDetail.evaluation.is_excellent ? '是' : '否' }}</el-descriptions-item>
            <el-descriptions-item label="评语" :span="2">{{ studentDetail.evaluation.overall_feedback }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
      <el-empty v-else description="暂无数据" />
    </el-drawer>
  </div>
</template>

<script setup name="ClassOverview">
import { CircleCheck, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listTeacherTask } from '@/api/learning/task'
import { getClassOverview, getStudentDetail } from '@/api/learning/monitor'

const loading = ref(false)
const showSearch = ref(true)
const overview = ref({})
const studentList = ref([])
const taskOptions = ref([])
const detailVisible = ref(false)
const studentDetail = ref({})

const queryParams = ref({
  taskId: undefined
})

function stageLabel(stage) {
  const key = String(stage || '')
  return { scenario: '情境', decision: '决策', reflection: '反思', research: '研究', submitted: '已提交', completed: '已完成' }[key] || key
}

function stageTagType(stage) {
  const key = String(stage || '')
  return { scenario: 'info', decision: 'warning', reflection: 'primary', research: 'success', submitted: 'success', completed: 'success' }[key] || 'info'
}

function stageCount(stage) {
  const dist = overview.value.stage_distribution || {}
  return dist[stage] || 0
}

async function loadTaskOptions() {
  const res = await listTeacherTask({ pageNum: 1, pageSize: 100 })
  const data = res?.data ?? {}
  const rows = Array.isArray(data.rows) ? data.rows : Array.isArray(res?.rows) ? res.rows : []
  taskOptions.value = rows.map(r => ({
    task_id: r.task_id ?? r.taskId,
    task_name: r.task_name ?? r.taskName
  }))
}

function handleQuery() {
  if (!queryParams.value.taskId) {
    ElMessage.warning('请先选择一个教学任务')
    return
  }
  loading.value = true
  getClassOverview(queryParams.value.taskId)
    .then(res => {
      const data = res?.data ?? {}
      overview.value = data
      studentList.value = data.students || []
    })
    .finally(() => {
      loading.value = false
    })
}

function resetQuery() {
  queryParams.value.taskId = undefined
  overview.value = {}
  studentList.value = []
}

async function viewDetail(row) {
  const res = await getStudentDetail(row.record_id)
  studentDetail.value = res?.data ?? {}
  detailVisible.value = true
}

onMounted(() => {
  loadTaskOptions()
})
</script>

<style scoped>
.mb8 { margin-bottom: 12px; }
.mt8 { margin-top: 8px; }
.mr4 { margin-right: 4px; }
.card-header { font-weight: bold; }
</style>
