<template>
  <div class="app-container">
    <el-table v-loading="loading" :data="caseList">
      <el-table-column label="案例ID" prop="case_id" width="90" />
      <el-table-column label="情境摘要" min-width="300" show-overflow-tooltip>
        <template #default="scope">
          {{ scope.row.scenario_desc || '暂无描述' }}
        </template>
      </el-table-column>
      <el-table-column label="标签" width="200">
        <template #default="scope">
          <el-tag v-for="(tag, i) in (scope.row.tags || [])" :key="i" size="small" class="mr4">{{ tag }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="create_time" width="170" />
      <el-table-column label="操作" width="140" align="center">
        <template #default="scope">
          <el-button type="primary" link icon="View" @click="viewDetail(scope.row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 案例详情抽屉 -->
    <el-drawer v-model="detailVisible" title="优秀案例详情" size="50%">
      <div v-if="caseDetail.case_id">
        <el-card class="mb12">
          <template #header><strong>情境描述</strong></template>
          <p style="white-space: pre-wrap;">{{ caseDetail.scenario_desc }}</p>
        </el-card>

        <el-card class="mb12" v-if="caseDetail.decision_data">
          <template #header><strong>决策记录</strong></template>
          <pre style="white-space: pre-wrap;">{{ typeof caseDetail.decision_data === 'string' ? caseDetail.decision_data : JSON.stringify(caseDetail.decision_data, null, 2) }}</pre>
        </el-card>

        <el-card class="mb12" v-if="caseDetail.reflection_data">
          <template #header><strong>反思精华</strong></template>
          <p style="white-space: pre-wrap;">{{ caseDetail.reflection_data }}</p>
        </el-card>

        <el-card class="mb12" v-if="caseDetail.research_data">
          <template #header><strong>研究成果</strong></template>
          <p>{{ caseDetail.research_data }}</p>
        </el-card>

        <el-card v-if="caseDetail.teacher_comment">
          <template #header><strong>教师推荐语</strong></template>
          <p>{{ caseDetail.teacher_comment }}</p>
        </el-card>
      </div>
      <el-empty v-else description="暂无数据" />
    </el-drawer>
  </div>
</template>

<script setup name="CaseList">
import { listCases, getCaseDetail } from '@/api/learning/monitor'

const loading = ref(false)
const caseList = ref([])
const detailVisible = ref(false)
const caseDetail = ref({})

function getList() {
  loading.value = true
  listCases()
    .then(res => {
      caseList.value = res?.data ?? []
    })
    .finally(() => { loading.value = false })
}

async function viewDetail(row) {
  const res = await getCaseDetail(row.case_id)
  caseDetail.value = res?.data ?? {}
  detailVisible.value = true
}

onMounted(() => {
  getList()
})
</script>

<style scoped>
.mb12 { margin-bottom: 12px; }
.mr4 { margin-right: 4px; }
</style>
