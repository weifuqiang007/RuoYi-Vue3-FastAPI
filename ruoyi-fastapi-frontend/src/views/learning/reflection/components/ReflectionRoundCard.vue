<template>
  <el-card shadow="never" class="round-card history-round">
    <template #header>
      <div class="round-header">
        <div class="round-title">
          <el-tag type="info" size="small">
            第 {{ roundIndex + 1 }} 轮
          </el-tag>
          <span class="round-time">{{ time || '' }}</span>
        </div>
        <div v-if="depthScoreAfter !== null && depthScoreAfter !== undefined" class="depth-badge">
          <el-tag size="small" :type="depthTagType">
            深度 {{ depthScoreAfter }}
          </el-tag>
        </div>
      </div>
    </template>

    <!-- 深度变化指示 -->
    <div v-if="depthScoreBefore !== null && depthScoreAfter !== null" class="depth-change">
      <span class="depth-label">深度变化：</span>
      <span class="depth-before">{{ depthScoreBefore }}</span>
      <span class="depth-arrow">
        <el-icon><Right /></el-icon>
      </span>
      <span class="depth-after">{{ depthScoreAfter }}</span>
      <span v-if="depthDiff > 0" class="depth-diff up">(+{{ depthDiff }})</span>
      <span v-else-if="depthDiff < 0" class="depth-diff down">({{ depthDiff }})</span>
    </div>

    <!-- 对话内容 -->
    <div class="dialogue-content">
      <div v-if="parsedContent" class="content-text">
        <div v-if="typeof parsedContent === 'string'" v-html="formatText(parsedContent)" />
        <div v-else>
          <!-- 结构化内容展示 -->
          <div v-if="parsedContent.reflection_direction" class="section">
            <div class="section-title">💡 反思方向</div>
            <div class="direction-text">{{ parsedContent.reflection_direction }}</div>
          </div>
          <div v-if="theories.length" class="section">
            <div class="section-title">📖 关联理论</div>
            <div v-for="(t, idx) in theories" :key="idx" class="theory-item">
              <div class="theory-name">
                {{ t.theory_name || t.name || '理论' }}
                <span v-if="t.theory_source" class="theory-source">（{{ t.theory_source }}）</span>
              </div>
              <div v-if="t.relevance" class="theory-detail"><strong>关联：</strong>{{ t.relevance }}</div>
              <div v-if="t.suggestion" class="theory-detail"><strong>建议：</strong>{{ t.suggestion }}</div>
            </div>
          </div>
          <div v-if="questions.length" class="section">
            <div class="section-title">📌 追问</div>
            <div v-for="(q, idx) in questions" :key="idx" class="question-item">
              <el-tag size="small" type="primary">追问 {{ idx + 1 }}</el-tag>
              <div class="question-text">{{ formatQuestion(q) }}</div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="empty-content">暂无内容</div>
    </div>
  </el-card>
</template>

<script setup>
import { Right } from '@element-plus/icons-vue'

const props = defineProps({
  roundIndex: { type: Number, default: 0 },
  isCurrent: { type: Boolean, default: false },
  dialogueContent: { type: [String, Object], default: '' },
  depthScoreAfter: { type: Number, default: null },
  depthScoreBefore: { type: Number, default: null },
  time: { type: String, default: '' }
})

const depthDiff = computed(() => {
  if (props.depthScoreBefore == null || props.depthScoreAfter == null) return 0
  return props.depthScoreAfter - props.depthScoreBefore
})

const depthTagType = computed(() => {
  const s = props.depthScoreAfter ?? 0
  if (s >= 4) return 'success'
  if (s >= 2) return 'warning'
  return 'info'
})

const parsedContent = computed(() => {
  if (!props.dialogueContent) return null
  if (typeof props.dialogueContent === 'object') return props.dialogueContent
  try {
    return JSON.parse(props.dialogueContent)
  } catch {
    return props.dialogueContent
  }
})

const theories = computed(() => {
  const d = parsedContent.value
  if (!d || typeof d === 'string') return []
  const g = d.theory_guidance || d.theories || []
  return Array.isArray(g) ? g : []
})

const questions = computed(() => {
  const d = parsedContent.value
  if (!d || typeof d === 'string') return []
  const q = d.questions || []
  return Array.isArray(q) ? q : []
})

function formatText(text) {
  return text.replace(/\n/g, '<br>')
}

function formatQuestion(q) {
  if (typeof q === 'string') return q
  return q?.question || q?.content || JSON.stringify(q)
}
</script>

<style scoped>
.round-card.history-round {
  border-left: 3px solid #909399;
  margin-bottom: 8px;
}
.round-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.round-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.round-time {
  font-size: 12px;
  color: #909399;
}
.depth-change {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 10px;
  font-size: 13px;
  color: #606266;
}
.depth-label {
  color: #909399;
}
.depth-arrow {
  color: #c0c4cc;
}
.depth-diff.up {
  color: #67c23a;
  font-weight: 600;
}
.depth-diff.down {
  color: #f56c6c;
  font-weight: 600;
}
.dialogue-content {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}
.content-text {
  white-space: pre-wrap;
  word-break: break-word;
}
.empty-content {
  color: #c0c4cc;
  text-align: center;
  padding: 10px 0;
}

/* 结构化内容样式 */
.section {
  margin-bottom: 12px;
}
.section:last-child {
  margin-bottom: 0;
}
.section-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
  color: #303133;
}
.theory-item {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 8px;
}
.theory-item:last-child {
  margin-bottom: 0;
}
.theory-name {
  font-weight: 600;
  font-size: 14px;
  color: #409eff;
  margin-bottom: 4px;
}
.theory-source {
  color: #909399;
  font-weight: normal;
  font-size: 12px;
}
.theory-detail {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-top: 4px;
}
.direction-text {
  background: #ecf5ff;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
.question-item {
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px 12px;
}
.question-item:last-child {
  margin-bottom: 0;
}
.question-text {
  margin-top: 6px;
  white-space: pre-wrap;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}
</style>
