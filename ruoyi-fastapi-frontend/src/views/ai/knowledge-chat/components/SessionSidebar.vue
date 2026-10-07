<template>
  <div class="session-sidebar">
    <div class="sidebar-header">
      <el-button type="primary" class="new-session-btn" icon="Plus" @click="$emit('new-session')">
        新建会话
      </el-button>
    </div>

    <div v-loading="loading" class="session-list">
      <div
        v-for="session in sessions"
        :key="session.sessionId"
        :class="['session-item', { active: session.sessionId === activeSessionId }]"
        @click="$emit('select', session)"
      >
        <div class="session-title">{{ session.title || "新会话" }}</div>
        <div class="session-time">{{ formatTime(session.updatedAt || session.createdAt) }}</div>
      </div>
      <div v-if="!loading && sessions.length === 0" class="session-empty">暂无历史会话</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  sessions: {
    type: Array,
    default: () => [],
  },
  activeSessionId: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

defineEmits(["new-session", "select"]);

function formatTime(timeStr) {
  if (!timeStr) return "";
  const date = new Date(timeStr);
  if (Number.isNaN(date.getTime())) return timeStr;
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
</script>

<style scoped>
.session-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}
.sidebar-header {
  padding: 12px;
}
.new-session-btn {
  width: 100%;
}
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
}
.session-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 2px;
}
.session-item:hover {
  background: var(--el-fill-color-light);
}
.session-item.active {
  background: var(--el-color-primary-light-9);
}
.session-title {
  font-size: 14px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.session-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}
.session-empty {
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  padding: 24px 0;
}
</style>
