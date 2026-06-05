<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>反思日志</span>
        <div class="actions">
          <slot name="actions" />
        </div>
      </div>
    </template>
    <el-input
      v-model="content"
      type="textarea"
      :rows="14"
      placeholder="写下你的反思：发生了什么？为什么？你在其中的立场、价值与关系是什么？"
      @blur="emitBlur"
    />
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue', 'blur'])

const content = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

function emitBlur() {
  emit('blur')
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
</style>

