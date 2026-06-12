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

const stages = ['scenario', 'decision', 'reflection', 'research']

const activeIndex = computed(() => {
  const index = stages.indexOf(props.currentStage || 'scenario')
  return index >= 0 ? index : stages.length
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
