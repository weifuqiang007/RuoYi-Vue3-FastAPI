<template>
  <el-card shadow="never">
    <template #header>
      <div class="module-title">
        <span class="bar" />
        <span class="text">关键事件</span>
      </div>
    </template>
    <div v-if="events.length === 0" class="empty">暂无结果</div>
    <el-timeline v-else class="timeline">
      <el-timeline-item
        v-for="(e, idx) in events"
        :key="idx"
        class="timeline-item"
      >
        <template #dot>
          <div class="dot">{{ idx + 1 }}</div>
        </template>
        <div class="event-card">
          <div class="event-label">事件 {{ idx + 1 }}</div>
          <div class="event-body">{{ formatEvent(e) }}</div>
        </div>
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
  const obj = normalizeMaybeJson(e)
  if (typeof obj === 'string') return obj
  return (
    obj?.event ??
    obj?.desc ??
    obj?.content ??
    obj?.text ??
    (obj ? JSON.stringify(obj) : '')
  )
}

function normalizeMaybeJson(v) {
  if (!v) return ''
  if (typeof v !== 'string') return v
  const s = v.trim()
  if (!s) return ''
  if (s.startsWith('{') && s.endsWith('}')) {
    try {
      return JSON.parse(s)
    } catch {
      return s
    }
  }
  return s
}
</script>

<style scoped>
.module-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
}
.bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: #3b82f6;
}
.timeline :deep(.el-timeline-item__tail) {
  border-left-color: rgba(59, 130, 246, 0.35);
}
.timeline-item {
  padding-bottom: 18px;
}
.dot {
  width: 22px;
  height: 22px;
  border-radius: 9999px;
  background: #3b82f6;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}
.event-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  padding: 16px;
}
.event-label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}
.event-body {
  font-size: 15px;
  color: #1f2937;
  line-height: 1.6;
  white-space: pre-wrap;
}
.empty {
  color: #909399;
  padding: 16px 0;
  text-align: center;
}
</style>
