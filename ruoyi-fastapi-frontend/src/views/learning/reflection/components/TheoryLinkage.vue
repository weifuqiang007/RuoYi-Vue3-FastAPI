<template>
  <el-card shadow="never">
    <template #header>关联理论总览</template>
    <div v-if="theories.length === 0" class="empty">暂无关联理论</div>
    <div v-else class="theories-list">
      <div v-for="(t, idx) in theories" :key="idx" class="theory-card">
        <div class="theory-name">
          {{ getTheoryName(t) }}
          <span v-if="getTheorySource(t)" class="theory-source">（{{ getTheorySource(t) }}）</span>
        </div>
        <div v-if="getRelevance(t)" class="theory-relevance">
          <strong>关联说明：</strong>{{ getRelevance(t) }}
        </div>
        <div v-if="getSuggestion(t)" class="theory-suggestion">
          <strong>反思建议：</strong>{{ getSuggestion(t) }}
        </div>
        <div v-if="getDescription(t) && !getRelevance(t) && !getSuggestion(t)" class="theory-desc">
          {{ getDescription(t) }}
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  theories: { type: Array, default: () => [] }
})

function getTheoryName(t) {
  if (typeof t === 'string') return t
  return t?.theory_name || t?.name || t?.title || '理论'
}

function getTheorySource(t) {
  if (typeof t === 'string') return ''
  return t?.theory_source || ''
}

function getRelevance(t) {
  if (typeof t === 'string') return ''
  return t?.relevance || ''
}

function getSuggestion(t) {
  if (typeof t === 'string') return ''
  return t?.suggestion || ''
}

function getDescription(t) {
  if (typeof t === 'string') return ''
  return t?.description || ''
}
</script>

<style scoped>
.empty {
  color: #909399;
  padding: 14px 0;
  text-align: center;
}
.theories-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.theory-card {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 10px 12px;
}
.theory-name {
  font-weight: 600;
  font-size: 14px;
  color: #409eff;
  margin-bottom: 6px;
}
.theory-source {
  color: #909399;
  font-weight: normal;
  font-size: 12px;
}
.theory-relevance, .theory-suggestion {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-top: 4px;
}
.theory-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
</style>
