<template>
  <el-card shadow="never">
    <template #header>深度演变</template>
    <div v-if="points.length === 0" class="empty">暂无数据</div>
    <div v-else ref="chartRef" style="height: 260px" />
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
      score: Number(item.depth_score ?? item.depthScore ?? 0)
    }))
    .filter(p => p.time)
})

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
</style>

