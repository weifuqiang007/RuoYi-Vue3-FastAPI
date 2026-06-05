<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>{{ title }}</span>
        <div class="actions">
          <el-button size="small" :loading="drafting" @click="$emit('draft')">AI 辅助撰写</el-button>
          <el-button size="small" type="primary" :loading="saving" @click="$emit('save')">保存</el-button>
        </div>
      </div>
    </template>

    <el-input v-model="content" type="textarea" :rows="12" placeholder="章节内容..." />
    <div v-if="aiSuggestion" class="suggestion">
      <div class="suggestion-title">AI 建议</div>
      <div class="suggestion-content">{{ aiSuggestion }}</div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  title: { type: String, default: '章节' },
  aiSuggestion: { type: String, default: '' },
  saving: { type: Boolean, default: false },
  drafting: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue', 'save', 'draft'])

const content = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
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
.suggestion {
  margin-top: 12px;
  padding: 12px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
}
.suggestion-title {
  font-weight: 600;
  margin-bottom: 8px;
}
.suggestion-content {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #606266;
}
</style>

