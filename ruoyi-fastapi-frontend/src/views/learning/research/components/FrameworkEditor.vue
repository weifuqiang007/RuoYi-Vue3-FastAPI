<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>论文框架</span>
        <div class="actions">
          <slot name="actions" />
        </div>
      </div>
    </template>

    <!-- 流式生成过程 -->
    <div v-if="streamText" class="stream-preview">{{ streamText }}<span class="cursor">|</span></div>
    <!-- 可读章节大纲 -->
    <div v-else-if="frameworkList.length" class="framework-list">
      <div v-for="item in frameworkList" :key="item.index" class="framework-item">
        <div class="item-title">
          <span class="item-index">{{ item.index }}.</span>
          <span class="item-name">{{ item.title }}</span>
        </div>
        <div v-if="item.description" class="item-desc">{{ item.description }}</div>
      </div>
    </div>
    <!-- 空状态 -->
    <div v-else class="empty">暂无框架</div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [Object, Array, String], default: null },
  streamText: { type: String, default: '' }
})

const frameworkList = computed(() => {
  if (!props.modelValue) return []
  if (Array.isArray(props.modelValue)) return props.modelValue
  if (typeof props.modelValue === 'string') {
    try {
      const parsed = JSON.parse(props.modelValue)
      if (Array.isArray(parsed)) return parsed
    } catch {
      return []
    }
  }
  return []
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
.stream-preview {
  min-height: 120px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
  color: #303133;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.cursor {
  animation: blink 1s infinite;
  color: #409eff;
  font-weight: bold;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.framework-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.framework-item {
  padding: 10px 14px;
  border-left: 3px solid #409eff;
  margin-bottom: 8px;
  background: #fafcff;
  border-radius: 0 6px 6px 0;
}
.framework-item:last-child {
  margin-bottom: 0;
}
.item-title {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.item-index {
  font-weight: 700;
  color: #409eff;
  font-size: 16px;
  min-width: 24px;
}
.item-name {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}
.item-desc {
  margin-top: 6px;
  padding-left: 30px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
</style>
