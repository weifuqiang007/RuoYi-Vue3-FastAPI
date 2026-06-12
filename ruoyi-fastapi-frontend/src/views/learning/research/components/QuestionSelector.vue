<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>候选研究问题</span>
        <div class="actions">
          <slot name="actions" />
        </div>
      </div>
    </template>

    <!-- 流式生成中 -->
    <div v-if="streamText" class="stream-preview">{{ streamText }}<span class="cursor">|</span></div>
    <!-- 空状态 -->
    <div v-else-if="questions.length === 0" class="empty">暂无候选问题</div>
    <!-- 卡片列表 -->
    <div v-else class="question-list">
      <div
        v-for="(q, idx) in questions"
        :key="idx"
        class="question-card"
        :class="{ selected: isSelected(q) }"
        @click="select(q)"
      >
        <!-- 核心问题（始终可见） -->
        <div class="question-header">
          <span class="question-index">{{ idx + 1 }}.</span>
          <span class="question-text">{{ formatQuestion(q) }}</span>
        </div>
        <!-- 展开/收起提示 -->
        <div class="toggle-hint" @click.stop="toggleExpand(idx)">
          <span v-if="!expanded.has(idx)" class="hint-text">▸ 点击查看详情</span>
          <span v-else class="hint-text">▾ 收起详情</span>
        </div>
        <!-- 展开后：详细说明 -->
        <div v-if="expanded.has(idx)" class="question-detail">
          <div v-if="getRationale(q)" class="detail-item">
            <span class="detail-label">选择理由：</span>
            <span class="detail-content">{{ getRationale(q) }}</span>
          </div>
          <div v-if="getApproach(q)" class="detail-item">
            <span class="detail-label">研究路径：</span>
            <span class="detail-content">{{ getApproach(q) }}</span>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  questions: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
  streamText: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const expanded = ref(new Set())

function formatQuestion(q) {
  if (typeof q === 'string') return q
  if (q?.question) return q.question
  if (q?.content) return q.content
  return JSON.stringify(q)
}

function getRationale(q) {
  return typeof q === 'object' ? (q.rationale || '') : ''
}

function getApproach(q) {
  return typeof q === 'object' ? (q.approach || '') : ''
}

function isSelected(q) {
  return props.modelValue === formatQuestion(q)
}

function select(q) {
  emit('update:modelValue', formatQuestion(q))
}

function toggleExpand(idx) {
  const s = new Set(expanded.value)
  if (s.has(idx)) {
    s.delete(idx)
  } else {
    s.add(idx)
  }
  expanded.value = s
}
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

.question-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.question-card {
  padding: 12px 14px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.question-card:hover {
  border-color: #b3d8ff;
  background: #f5f9ff;
}
.question-card.selected {
  border-color: #409eff;
  background: #ecf5ff;
}
.question-header {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}
.question-index {
  font-weight: 700;
  color: #409eff;
  flex-shrink: 0;
  min-width: 20px;
}
.question-text {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  word-break: break-word;
}
.toggle-hint {
  margin-top: 6px;
  padding-left: 26px;
}
.hint-text {
  font-size: 12px;
  color: #409eff;
  cursor: pointer;
}
.hint-text:hover {
  text-decoration: underline;
}
.question-detail {
  margin-top: 10px;
  padding: 10px 12px;
  background: #fff;
  border-radius: 6px;
  border: 1px dashed #dcdfe6;
}
.detail-item {
  margin-bottom: 8px;
  line-height: 1.7;
  font-size: 13px;
}
.detail-item:last-child {
  margin-bottom: 0;
}
.detail-label {
  font-weight: 600;
  color: #606266;
}
.detail-content {
  color: #909399;
}
</style>
