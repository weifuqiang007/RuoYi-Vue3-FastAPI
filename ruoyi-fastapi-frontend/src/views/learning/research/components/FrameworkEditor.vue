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

    <div v-if="!modelValueText" class="empty">暂无框架</div>
    <el-input
      v-else
      v-model="text"
      type="textarea"
      :rows="10"
      placeholder="框架 JSON..."
    />
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [Object, Array, String], default: null }
})
const emit = defineEmits(['update:modelValue'])

const modelValueText = computed(() => {
  if (!props.modelValue) return ''
  if (typeof props.modelValue === 'string') return props.modelValue
  return JSON.stringify(props.modelValue, null, 2)
})

const text = computed({
  get: () => modelValueText.value,
  set: (v) => {
    try {
      emit('update:modelValue', JSON.parse(v))
    } catch {
      emit('update:modelValue', v)
    }
  }
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
</style>

