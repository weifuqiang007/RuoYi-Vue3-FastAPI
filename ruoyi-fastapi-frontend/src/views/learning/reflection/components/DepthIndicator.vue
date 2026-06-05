<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>反思深度</span>
        <span class="meta">{{ scoreText }}（{{ levelText }}）</span>
      </div>
    </template>
    <el-progress :percentage="percentage" :status="progressStatus" />
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  depthScore: { type: [Number, String], default: 0 },
  depthLevel: { type: String, default: '' }
})

const scoreValue = computed(() => {
  const v = Number(props.depthScore)
  return Number.isFinite(v) ? Math.max(0, Math.min(1, v)) : 0
})

const percentage = computed(() => Math.round(scoreValue.value * 100))

const levelText = computed(() => {
  const key = String(props.depthLevel || '')
  if (!key) {
    if (scoreValue.value >= 0.71) return '反身性'
    if (scoreValue.value >= 0.41) return '分析性'
    if (scoreValue.value >= 0.2) return '描述性'
    return '起步'
  }
  return { descriptive: '描述性', analytical: '分析性', reflexive: '反身性' }[key] || key
})

const scoreText = computed(() => scoreValue.value.toFixed(2))

const progressStatus = computed(() => {
  if (scoreValue.value >= 0.71) return 'success'
  if (scoreValue.value >= 0.41) return ''
  return 'warning'
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.meta {
  color: #909399;
  font-size: 12px;
}
</style>

