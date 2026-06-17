<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>材料汇总</span>
        <div class="actions">
          <el-button size="small" @click="editMode = !editMode">
            {{ editMode ? '完成编辑' : '编辑' }}
          </el-button>
          <slot name="actions" />
        </div>
      </div>
    </template>

    <!-- 编辑模式：原始文本框 -->
    <el-input
      v-if="editMode"
      v-model="innerText"
      type="textarea"
      :rows="16"
      placeholder="前三区材料汇总（可编辑）..."
      resize="vertical"
    />

    <!-- 卡片展示模式 -->
    <div v-else-if="sections.hasContent" class="material-cards">
      <!-- 情境 -->
      <div v-if="sections.scenario" class="block scenario-block">
        <div class="block-title"><span class="icon">📍</span> 情境</div>
        <div class="block-content">{{ sections.scenario }}</div>
      </div>

      <!-- 决策（每个一条便签） -->
      <div v-if="sections.decisions.length" class="block decisions-block">
        <div class="block-title"><span class="icon">🎯</span> 决策（共 {{ sections.decisions.length }} 条）</div>
        <div class="decision-notes">
          <div v-for="(d, i) in sections.decisions" :key="i" class="decision-note">
            <div class="note-header">📌 决策 {{ i + 1 }}</div>
            <div v-if="d.event" class="note-row">
              <span class="note-label">关键事件</span>
              <span class="note-text">{{ d.event }}</span>
            </div>
            <div v-if="d.action" class="note-row">
              <span class="note-label">采取行动</span>
              <span class="note-text">{{ d.action }}</span>
            </div>
            <div v-if="d.reasoning" class="note-row">
              <span class="note-label">行动理由</span>
              <span class="note-text">{{ d.reasoning }}</span>
            </div>
            <div v-if="d.outcome" class="note-row">
              <span class="note-label">实际结果</span>
              <span class="note-text">{{ d.outcome }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 反思 -->
      <div v-if="sections.reflection" class="block reflection-block">
        <div class="block-title"><span class="icon">💭</span> 反思</div>
        <div class="block-content">{{ sections.reflection }}</div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty">暂无材料，点击"重新汇总"生成</div>
  </el-card>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const editMode = ref(false)

const innerText = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

// 解析材料文本为结构化区块
const sections = computed(() => {
  const text = props.modelValue || ''
  const result = { scenario: '', decisions: [], reflection: '', hasContent: false }

  // 情境
  const scenarioMatch = text.match(/【情境】([\s\S]*?)(?=【决策】|【反思】|$)/)
  if (scenarioMatch) result.scenario = scenarioMatch[1].trim()

  // 决策
  const decisionMatch = text.match(/【决策】([\s\S]*?)(?=【反思】|$)/)
  if (decisionMatch) {
    const body = decisionMatch[1]
    // 按决策块拆分
    const blocks = body.split(/【决策\d+】/).slice(1)
    for (const block of blocks) {
      const cleanBlock = block.replace(/^共\s*\d+\s*条决策记录[：:]?/, '').trim()
      const d = {}
      const eventM = cleanBlock.match(/关键事件[：:]\s*([\s\S]*?)(?=采取行动|行动理由|实际结果|$)/)
      const actionM = cleanBlock.match(/采取行动[：:]\s*([\s\S]*?)(?=关键事件|行动理由|实际结果|$)/)
      const reasoningM = cleanBlock.match(/行动理由[：:]\s*([\s\S]*?)(?=关键事件|采取行动|实际结果|$)/)
      const outcomeM = cleanBlock.match(/实际结果[：:]\s*([\s\S]*?)(?=关键事件|采取行动|行动理由|$)/)
      if (eventM) d.event = eventM[1].trim()
      if (actionM) d.action = actionM[1].trim()
      if (reasoningM) d.reasoning = reasoningM[1].trim()
      if (outcomeM) d.outcome = outcomeM[1].trim()
      if (Object.keys(d).length) result.decisions.push(d)
    }
  }

  // 反思
  const reflectionMatch = text.match(/【反思】([\s\S]*?)$/)
  if (reflectionMatch) result.reflection = reflectionMatch[1].trim()

  result.hasContent = !!(result.scenario || result.decisions.length || result.reflection)
  return result
})
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
  padding: 14px 0;
  text-align: center;
}

.material-cards {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.block {
  border-radius: 8px;
  overflow: hidden;
}
.block-title {
  font-weight: 700;
  font-size: 15px;
  padding: 8px 14px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 6px;
}
.block-title .icon {
  font-size: 16px;
}
.block-content {
  padding: 12px 14px;
  white-space: pre-wrap;
  line-height: 1.8;
  word-break: break-word;
}

/* 情境：蓝色框 */
.scenario-block {
  border: 1px solid #d9ecff;
  background: #f4f9ff;
}
.scenario-block .block-title {
  background: #409eff;
}
.scenario-block .block-content {
  color: #303133;
}

/* 决策区容器 */
.decisions-block .block-title {
  background: #67c23a;
}
.decision-notes {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  background: #f0f9eb;
}

/* 决策便签 */
.decision-note {
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-left: 4px solid #faad14;
  border-radius: 6px;
  padding: 12px 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s, transform 0.2s;
}
.decision-note:hover {
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}
.note-header {
  font-weight: 700;
  font-size: 14px;
  color: #d48806;
  margin-bottom: 8px;
}
.note-row {
  margin-bottom: 8px;
  line-height: 1.7;
}
.note-row:last-child {
  margin-bottom: 0;
}
.note-label {
  display: inline-block;
  background: #faad14;
  color: #fff;
  font-size: 12px;
  padding: 1px 8px;
  border-radius: 10px;
  margin-right: 8px;
  font-weight: 600;
  vertical-align: middle;
}
.note-text {
  color: #595959;
  word-break: break-word;
}

/* 反思：紫色框 */
.reflection-block {
  border: 1px solid #d3adf7;
  background: #f9f0ff;
}
.reflection-block .block-title {
  background: #722ed1;
}
.reflection-block .block-content {
  color: #303133;
}
</style>
