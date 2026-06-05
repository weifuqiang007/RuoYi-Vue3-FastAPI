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

    <div v-if="questions.length === 0" class="empty">暂无候选问题</div>
    <el-radio-group v-else v-model="selected" class="list">
      <el-radio v-for="(q, idx) in questions" :key="idx" :value="formatQuestion(q)" class="item">
        {{ formatQuestion(q) }}
      </el-radio>
    </el-radio-group>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  questions: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const selected = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

function formatQuestion(q) {
  if (typeof q === 'string') return q
  if (q?.question) return q.question
  if (q?.content) return q.content
  return JSON.stringify(q)
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
.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.item {
  align-items: flex-start;
  white-space: normal;
  line-height: 1.6;
}
</style>

