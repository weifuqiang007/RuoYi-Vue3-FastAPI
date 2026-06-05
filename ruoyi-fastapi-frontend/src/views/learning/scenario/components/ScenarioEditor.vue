<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>场景描述</span>
        <div class="actions">
          <slot name="actions" />
        </div>
      </div>
    </template>
    <el-input
      v-model="content"
      type="textarea"
      :rows="10"
      placeholder="描述你在实习/实践中遇到的真实情境..."
      @blur="emitBlur"
    />
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
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

