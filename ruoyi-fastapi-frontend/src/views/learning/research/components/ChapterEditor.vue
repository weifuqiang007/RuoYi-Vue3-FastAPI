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
    <!-- 流式 AI 建议（生成中）— Markdown 渲染 -->
    <div v-if="draftStreamText" class="suggestion">
      <div class="suggestion-title">AI 建议（生成中...）</div>
      <div class="suggestion-content">
        <MarkdownRender :content="draftStreamText" />
        <span class="cursor">|</span>
      </div>
    </div>
    <!-- 已完成的 AI 建议 — Markdown 渲染 -->
    <div v-else-if="aiSuggestion" class="suggestion">
      <div class="suggestion-title">AI 建议</div>
      <div class="suggestion-content">
        <MarkdownRender :content="aiSuggestion" />
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed, watch } from 'vue'
import { MarkdownRender } from 'markstream-vue'
import 'markstream-vue/index.css'

const props = defineProps({
  modelValue: { type: String, default: '' },
  title: { type: String, default: '章节' },
  aiSuggestion: { type: String, default: '' },
  saving: { type: Boolean, default: false },
  drafting: { type: Boolean, default: false },
  draftStreamText: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue', 'save', 'draft'])

const content = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

watch(
  () => props.aiSuggestion,
  (suggestion) => {
    if (!props.modelValue && suggestion) {
      emit('update:modelValue', suggestion)
    }
  },
  { immediate: true }
)
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
  line-height: 1.6;
  color: #606266;
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
</style>
