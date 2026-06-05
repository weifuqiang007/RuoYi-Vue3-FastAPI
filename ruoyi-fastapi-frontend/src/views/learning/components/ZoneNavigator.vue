<template>
  <div class="zone-navigator">
    <el-steps :active="activeIndex" align-center finish-status="success">
      <el-step title="情境区" @click="emitSelect('scenario')" />
      <el-step title="决策区" @click="emitSelect('decision')" />
      <el-step title="反思区" @click="emitSelect('reflection')" />
      <el-step title="研究生成区" @click="emitSelect('research')" />
    </el-steps>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentStage: {
    type: String,
    default: 'scenario'
  }
})

const emit = defineEmits(['select'])

const activeIndex = computed(() => {
  const stage = props.currentStage || 'scenario'
  return ['scenario', 'decision', 'reflection', 'research'].indexOf(stage)
})

function emitSelect(stage) {
  emit('select', stage)
}
</script>

<style scoped>
.zone-navigator :deep(.el-step__title) {
  cursor: pointer;
}
</style>

