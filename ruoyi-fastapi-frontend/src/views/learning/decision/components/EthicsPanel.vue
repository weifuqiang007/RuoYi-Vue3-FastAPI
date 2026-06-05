<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>AI 伦理分析</span>
        <div class="actions">
          <el-button type="primary" :loading="loading" :disabled="!decisionId" @click="analyze">生成分析</el-button>
        </div>
      </div>
    </template>

    <div v-if="!decisionId" class="empty">请选择或保存一条决策记录后再生成分析</div>
    <div v-else-if="!analysis" class="empty">暂无结果</div>
    <pre v-else class="json">{{ pretty }}</pre>
  </el-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ethicsAnalyzeDecision } from '@/api/learning/decision'

const props = defineProps({
  decisionId: { type: [String, Number], default: null },
  analysis: { type: [Object, Array, String], default: null }
})
const emit = defineEmits(['update:analysis'])

const loading = ref(false)

const pretty = computed(() => {
  if (typeof props.analysis === 'string') return props.analysis
  return JSON.stringify(props.analysis, null, 2)
})

async function analyze() {
  if (!props.decisionId) return
  loading.value = true
  try {
    const res = await ethicsAnalyzeDecision({ decision_id: props.decisionId })
    emit('update:analysis', res.data ?? null)
  } finally {
    loading.value = false
  }
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
  padding: 16px 0;
  text-align: center;
}
.json {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

