<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>AI 伦理分析</span>
        <div class="actions">
          <el-button type="primary" :loading="loading" :disabled="!decisionId" @click="analyze">
            {{ analysis ? '重新分析' : '生成分析' }}
          </el-button>
        </div>
      </div>
    </template>

    <!-- 无决策记录 -->
    <div v-if="!decisionId" class="empty">请选择或保存一条决策记录后再生成分析</div>

    <!-- 加载中 -->
    <div v-else-if="loading" class="loading-wrap">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>AI 正在分析你的决策，请稍候（约30-60秒）...</span>
    </div>

    <!-- 无结果 -->
    <div v-else-if="!analysis" class="empty">点击「生成分析」按钮，AI 将从伦理角度分析你的决策</div>

    <!-- 结构化展示分析结果 -->
    <div v-else class="analysis-result">

      <!-- 一、综合分析 -->
      <div class="section">
        <div class="section-title">📋 综合分析</div>
        <div class="analysis-text">{{ result.analysis }}</div>
      </div>

      <!-- 二、伦理维度 -->
      <div v-if="result.ethics_dimensions?.length" class="section">
        <div class="section-title">⚖️ 伦理维度分析</div>
        <div class="dimension-list">
          <div
            v-for="(dim, idx) in result.ethics_dimensions"
            :key="idx"
            class="dimension-item"
          >
            <div class="dim-header">
              <span class="dim-name">{{ dim.name }}</span>
              <el-tag
                :type="dim.stance === '支持' ? 'success' : 'warning'"
                size="small"
                effect="dark"
              >
                {{ dim.stance }}
              </el-tag>
            </div>
            <div class="dim-desc">{{ dim.description }}</div>
          </div>
        </div>
      </div>

      <!-- 三、相关伦理守则 -->
      <div v-if="result.relevant_codes?.length" class="section">
        <div class="section-title">📖 相关伦理守则</div>
        <div class="code-list">
          <div
            v-for="(code, idx) in result.relevant_codes"
            :key="idx"
            class="code-item"
          >
            <div class="code-header">
              <el-tag type="info" size="small">{{ code.source }}</el-tag>
              <span class="code-name">{{ code.code }}</span>
            </div>
            <div class="code-relevance">{{ code.relevance }}</div>
          </div>
        </div>
      </div>

      <!-- 四、进一步思考 -->
      <div v-if="result.further_questions?.length" class="section">
        <div class="section-title">🤔 进一步思考</div>
        <div class="question-list">
          <div
            v-for="(q, idx) in result.further_questions"
            :key="idx"
            class="question-item"
          >
            <el-icon color="#409eff"><QuestionFilled /></el-icon>
            <span>{{ q }}</span>
          </div>
        </div>
      </div>

    </div>
  </el-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Loading, QuestionFilled } from '@element-plus/icons-vue'
import { ethicsAnalyzeDecision } from '@/api/learning/decision'

const props = defineProps({
  decisionId: { type: [String, Number], default: null },
  analysis: { type: [Object, Array, String], default: null }
})
const emit = defineEmits(['update:analysis'])

const loading = ref(false)

/** 将 analysis 统一为对象，兼容字符串/对象/异常格式 */
const result = computed(() => {
  const raw = props.analysis
  if (!raw) return {}
  if (typeof raw === 'string') {
    try { return JSON.parse(raw) } catch { return { analysis: raw } }
  }
  return raw
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
  padding: 24px 0;
  text-align: center;
  font-size: 14px;
}
.loading-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 0;
  color: #909399;
  font-size: 14px;
}
.loading-icon {
  font-size: 28px;
  color: #409eff;
  margin-bottom: 12px;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ====== 结构化展示样式 ====== */
.analysis-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.section {
  border-left: 3px solid #409eff;
  padding-left: 14px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

/* 综合分析文本 */
.analysis-text {
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 12px 16px;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 伦理维度 */
.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.dimension-item {
  background: #fafafa;
  border-radius: 6px;
  padding: 10px 14px;
  border: 1px solid #ebeef5;
}
.dim-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.dim-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.dim-desc {
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}

/* 伦理守则 */
.code-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.code-item {
  background: #f0f9eb;
  border-radius: 6px;
  padding: 10px 14px;
  border: 1px solid #e1f3d8;
}
.code-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.code-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.code-relevance {
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}

/* 进一步思考 */
.question-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.question-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  padding: 6px 10px;
  background: #ecf5ff;
  border-radius: 4px;
}
</style>
