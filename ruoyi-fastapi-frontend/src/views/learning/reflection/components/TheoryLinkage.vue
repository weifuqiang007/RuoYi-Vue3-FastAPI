<template>
  <el-card shadow="never">
    <template #header>相关理论</template>
    <div v-if="theories.length === 0" class="empty">暂无</div>
    <div v-else class="list">
      <el-tag v-for="(t, idx) in theories" :key="idx" class="item">{{ formatTheory(t) }}</el-tag>
    </div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  theories: { type: Array, default: () => [] }
})

function formatTheory(t) {
  if (typeof t === 'string') return t
  if (t?.name) return t.name
  if (t?.title) return t.title
  return JSON.stringify(t)
}
</script>

<style scoped>
.empty {
  color: #909399;
  padding: 14px 0;
  text-align: center;
}
.list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.item {
  margin: 0;
}
</style>

