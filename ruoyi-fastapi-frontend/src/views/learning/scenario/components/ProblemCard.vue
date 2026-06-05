<template>
  <el-card shadow="never">
    <template #header>专业问题识别</template>
    <div v-if="problems.length === 0" class="empty">暂无结果</div>
    <el-row v-else :gutter="12">
      <el-col v-for="(p, idx) in problems" :key="idx" :span="12">
        <el-card shadow="hover" class="problem-item">
          <div class="problem-title">问题 {{ idx + 1 }}</div>
          <div class="problem-content">{{ formatProblem(p) }}</div>
        </el-card>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup>
const props = defineProps({
  problems: {
    type: Array,
    default: () => []
  }
})

function formatProblem(p) {
  if (typeof p === 'string') return p
  if (p?.desc) return p.desc
  if (p?.content) return p.content
  return JSON.stringify(p)
}
</script>

<style scoped>
.empty {
  color: #909399;
  padding: 16px 0;
  text-align: center;
}
.problem-item {
  margin-bottom: 12px;
}
.problem-title {
  font-weight: 600;
  margin-bottom: 8px;
}
.problem-content {
  white-space: pre-wrap;
  color: #606266;
}
</style>

