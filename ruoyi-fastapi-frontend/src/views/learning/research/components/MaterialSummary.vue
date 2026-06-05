<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>材料汇总</span>
        <div class="actions">
          <slot name="actions" />
        </div>
      </div>
    </template>
    <div v-if="!text" class="empty">暂无材料</div>
    <div v-else class="content">{{ text }}</div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  text: { type: String, default: '' }
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.actions {
  display: flex;
  gap: 10px;
}
.empty {
  color: #909399;
  padding: 14px 0;
  text-align: center;
}
.content {
  white-space: pre-wrap;
  line-height: 1.7;
}
</style>

