<template>
  <div>
    <!-- 情境区 -->
    <el-card class="mb8">
      <template #header><span class="bold">情境区</span></template>
      <p v-if="scenario.description" class="pre">{{ scenario.description }}</p>
      <el-empty v-else description="暂无情境数据" :image-size="40" />
      <div v-if="scenario.key_events && scenario.key_events.length" class="mt8">
        <strong>关键事件：</strong>
        <el-tag v-for="(e, i) in scenario.key_events" :key="i" class="mr4" size="small">
          {{ formatKeyEvent(e) }}
        </el-tag>
      </div>
    </el-card>

    <!-- 决策区 -->
    <el-card class="mb8" v-if="decisions && decisions.length">
      <template #header><span class="bold">决策区（{{ decisions.length }}条）</span></template>
      <div v-for="(d, i) in decisions" :key="i" class="mb8">
        <p><strong>关键事件：</strong>{{ d.key_event_desc || '-' }}</p>
        <p><strong>采取行动：</strong>{{ d.action_taken || '-' }}</p>
        <p><strong>理由：</strong>{{ d.reasoning || '-' }}</p>
        <el-divider v-if="i < decisions.length - 1" />
      </div>
    </el-card>

    <!-- 反思区（核心批阅对象） -->
    <el-card class="mb8">
      <template #header><span class="bold">反思区（{{ reflections.length }}条 · 核心批阅对象）</span></template>
      <el-empty v-if="!reflections.length" description="暂无反思数据" :image-size="40" />
      <div v-for="(r, i) in reflections" :key="i" class="reflection-item">
        <div class="reflection-head">
          <span>反思 {{ i + 1 }}</span>
          <span class="depth-tag">
            <el-tag size="small" :type="depthTagType(r.depth_level)">{{ depthLabel(r.depth_level) }}</el-tag>
            <span class="score">{{ Number(r.depth_score ?? 0).toFixed(2) }}</span>
          </span>
        </div>
        <p class="pre">{{ r.content || '（空）' }}</p>
      </div>
    </el-card>

    <!-- 研究区 -->
    <el-card class="mb8" v-if="research && (research.selected_question || research.framework)">
      <template #header><span class="bold">研究生成区</span></template>
      <p><strong>研究问题：</strong>{{ research.selected_question || '-' }}</p>
    </el-card>
  </div>
</template>

<script setup name="StudentWorkPanel">
defineProps({
  scenario: { type: Object, default: () => ({}) },
  decisions: { type: Array, default: () => [] },
  reflections: { type: Array, default: () => [] },
  research: { type: Object, default: () => ({}) }
})

function formatKeyEvent(e) {
  if (!e) return ''
  if (typeof e === 'string') return e
  return e.event || e.desc || e.description || JSON.stringify(e)
}

function depthLabel(l) {
  return { descriptive: '描述性', analytical: '分析性', reflexive: '反身性' }[String(l || '')] || l || '-'
}

function depthTagType(l) {
  return { descriptive: 'info', analytical: 'warning', reflexive: 'success' }[String(l || '')] || 'info'
}
</script>

<style scoped>
.mb8 {
  margin-bottom: 12px;
}
.mt8 {
  margin-top: 8px;
}
.mr4 {
  margin-right: 4px;
}
.bold {
  font-weight: bold;
}
.pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 4px 0;
}
.reflection-item {
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
}
.reflection-item:last-child {
  border-bottom: none;
}
.reflection-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-weight: bold;
}
.depth-tag {
  display: flex;
  align-items: center;
  gap: 6px;
}
.score {
  color: #909399;
  font-size: 12px;
}
</style>
