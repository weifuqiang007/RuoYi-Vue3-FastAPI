<template>
  <el-card shadow="never">
    <template #header>关键事件</template>
    <div v-if="events.length === 0" class="empty">暂无结果</div>
    <el-timeline v-else>
      <el-timeline-item
        v-for="(e, idx) in events"
        :key="idx"
        :timestamp="`事件 ${idx + 1}`"
        placement="top"
      >
        <div class="event-text">{{ formatEvent(e) }}</div>
      </el-timeline-item>
    </el-timeline>
  </el-card>
</template>

<script setup>
const props = defineProps({
  events: {
    type: Array,
    default: () => []
  }
})

function formatEvent(e) {
  if (typeof e === 'string') return e
  if (e?.desc) return e.desc
  if (e?.content) return e.content
  return JSON.stringify(e)
}
</script>

<style scoped>
.empty {
  color: #909399;
  padding: 16px 0;
  text-align: center;
}
.event-text {
  white-space: pre-wrap;
}
</style>

