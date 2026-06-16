<template>
  <el-card shadow="never">
    <template #header>深度演变</template>
    <div v-if="points.length === 0" class="empty">暂无数据（保存或生成理论指导后会记录深度变化）</div>
    <template v-else>
      <div ref="chartRef" style="height: 220px" />

      <!-- 趋势与打分说明 -->
      <div class="depth-summary">
        <div class="summary-row">
          <span class="label">📈 趋势：</span>
          <span class="value">{{ analysis.trendText }}</span>
        </div>
        <div class="summary-row">
          <span class="label">🎯 当前层次：</span>
          <el-tag :type="analysis.levelTag" size="small">{{ analysis.levelLabel }}</el-tag>
          <span class="score">（{{ analysis.currentScoreText }}）</span>
        </div>

        <div class="summary-block">
          <div class="block-title">为什么是这个分数？</div>
          <div class="block-text">分数依据反思深度量表：</div>
          <ul class="rubric">
            <li><strong>描述性（0.20–0.40）</strong>：仅复述事件经过和个人感受</li>
            <li><strong>分析性（0.41–0.70）</strong>：开始分析事件原因、互动模式、策略选择</li>
            <li><strong>反身性（0.71–1.00）</strong>：审视自身价值观、立场、权力关系对实践的影响</li>
          </ul>
          <div class="block-text">{{ analysis.currentExplain }}</div>
        </div>

        <div class="summary-block">
          <div class="block-title">如何继续加深深度？</div>
          <div class="block-text">{{ analysis.deepenAdvice }}</div>
        </div>
      </div>
    </template>
  </el-card>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  history: { type: Array, default: () => [] }
})

const chartRef = ref(null)
let chartInstance = null

const points = computed(() => {
  if (!Array.isArray(props.history)) return []
  return props.history
    .map(item => ({
      time: item.create_time ?? item.createTime ?? '',
      score: Number(item.depth_score ?? item.depthScore ?? 0),
      level: item.depth_level ?? item.depthLevel ?? '',
    }))
    .filter(p => p.time)
})

/** 深度分析：趋势 + 当前层次 + 打分依据 + 加深建议 */
const analysis = computed(() => {
  const pts = points.value
  const last = pts[pts.length - 1] || { score: 0, level: '' }
  const score = last.score
  const level = levelOf(score, last.level)

  // 趋势
  let trendText = '当前为首次评估'
  if (pts.length >= 2) {
    const delta = pts[pts.length - 1].score - pts[0].score
    if (delta > 0.05) trendText = `深度从 ${pts[0].score.toFixed(2)} 上升到 ${score.toFixed(2)}（↑ 共 ${(delta).toFixed(2)}）`
    else if (delta < -0.05) trendText = `深度从 ${pts[0].score.toFixed(2)} 下降到 ${score.toFixed(2)}（↓ 共 ${(-delta).toFixed(2)}）`
    else trendText = `深度保持在 ${score.toFixed(2)} 附近，趋势平稳`
  }

  return {
    trendText,
    currentScoreText: score.toFixed(2),
    levelLabel: levelLabelOf(level),
    levelTag: levelTagOf(level),
    currentExplain: explainCurrent(level),
    deepenAdvice: deepenAdviceOf(level),
  }
})

function levelOf(score, fallback) {
  if (score >= 0.71) return 'reflexive'
  if (score >= 0.41) return 'analytical'
  if (score >= 0.20) return 'descriptive'
  return fallback || 'descriptive'
}
function levelLabelOf(level) {
  return { descriptive: '描述性', analytical: '分析性', reflexive: '反身性' }[level] || '描述性'
}
function levelTagOf(level) {
  return { descriptive: 'info', analytical: 'warning', reflexive: 'success' }[level] || 'info'
}
function explainCurrent(level) {
  return {
    descriptive: '你目前的分数说明反思主要停留在复述层面，尚未深入分析。',
    analytical: '你目前的分数说明已进入"分析"层次——能剖析原因、互动与策略。',
    reflexive: '你目前的分数说明已达到"反身性"层次——开始审视价值观与权力关系。',
  }[level] || ''
}
function deepenAdviceOf(level) {
  return {
    descriptive: '建议先从"描述"走向"分析"：剖析事件发生的原因、各方互动模式，以及你选择某种行动策略的依据。',
    analytical: '建议迈向"反身性"：进一步审视你在情境中的立场与价值取向、与服务对象的权力关系，以及这些如何影响了你的判断与行动。',
    reflexive: '你已达到反身性层次，建议持续结合专业理论，将反思沉淀为可迁移的实践智慧。',
  }[level] || ''
}

function render() {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value, 'macarons')
  }
  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: points.value.map(p => p.time) },
    yAxis: { type: 'value', min: 0, max: 1 },
    series: [
      {
        name: 'depth_score',
        type: 'line',
        smooth: true,
        data: points.value.map(p => p.score)
      }
    ]
  })
}

watch(
  () => points.value,
  async () => {
    await nextTick()
    if (points.value.length) {
      render()
    } else if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }
  },
  { deep: true, immediate: true }
)

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.empty {
  color: #909399;
  padding: 14px 0;
  text-align: center;
}
.depth-summary {
  margin-top: 12px;
  border-top: 1px dashed #ebeef5;
  padding-top: 12px;
}
.summary-row {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.summary-row .label {
  font-weight: 600;
  color: #303133;
}
.summary-row .score {
  color: #909399;
  margin-left: 4px;
}
.summary-block {
  margin-top: 10px;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 10px 12px;
}
.block-title {
  font-weight: 600;
  font-size: 13px;
  color: #409eff;
  margin-bottom: 6px;
}
.block-text {
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
}
.rubric {
  margin: 6px 0 6px 18px;
  padding: 0;
  font-size: 12.5px;
  color: #606266;
  line-height: 1.8;
}
.rubric li strong {
  color: #303133;
}
</style>
