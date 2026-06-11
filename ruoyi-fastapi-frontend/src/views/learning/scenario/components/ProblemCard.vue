<template>
  <el-card shadow="never">
    <template #header>
      <div class="module-title">
        <span class="bar" />
        <span class="text">专业问题识别</span>
      </div>
    </template>
    <div v-if="problems.length === 0" class="empty">暂无结果</div>
    <div v-else class="problem-grid">
      <div v-for="(p, idx) in problems" :key="idx" class="problem-card">
        <div class="problem-badge">问题 {{ idx + 1 }}</div>
        <div class="problem-title">{{ formatProblemTitle(p) }}</div>
        <div v-if="formatProblemDomain(p)" class="problem-domain">
          <span class="domain-badge">{{ formatProblemDomain(p) }}</span>
        </div>
        <div class="problem-desc">{{ formatProblemDesc(p) }}</div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  problems: {
    type: Array,
    default: () => []
  }
})

function formatProblemTitle(p) {
  const obj = normalizeMaybeJson(p)
  if (typeof obj === 'string') return obj
  return obj?.title ?? obj?.name ?? `问题`
}

function formatProblemDomain(p) {
  const obj = normalizeMaybeJson(p)
  if (typeof obj === 'string') return ''
  return obj?.domain ?? ''
}

function formatProblemDesc(p) {
  const obj = normalizeMaybeJson(p)
  if (typeof obj === 'string') return ''
  return obj?.description ?? obj?.desc ?? obj?.content ?? ''
}

function normalizeMaybeJson(v) {
  if (!v) return ''
  if (typeof v !== 'string') return v
  const s = v.trim()
  if (!s) return ''
  if (s.startsWith('{') && s.endsWith('}')) {
    try {
      return JSON.parse(s)
    } catch {
      return s
    }
  }
  return s
}
</script>

<style scoped>
.module-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
}
.bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: #3b82f6;
}
.empty {
  color: #909399;
  padding: 16px 0;
  text-align: center;
}
.problem-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
@media (max-width: 768px) {
  .problem-grid {
    grid-template-columns: 1fr;
  }
}
.problem-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 20px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.problem-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}
.problem-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 9999px;
  background: #eff6ff;
  color: #3b82f6;
  font-size: 13px;
  font-weight: 600;
}
.problem-title {
  margin-top: 8px;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}
.problem-domain {
  margin-bottom: 8px;
}
.domain-badge {
  display: inline-flex;
  padding: 4px 8px;
  border-radius: 6px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 12px;
}
.problem-desc {
  margin-top: 10px;
  font-size: 15px;
  color: #4b5563;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
