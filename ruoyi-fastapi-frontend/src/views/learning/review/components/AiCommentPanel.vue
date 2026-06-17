<template>
  <el-card>
    <template #header>
      <div class="head">
        <span class="bold">AI 评论（裁判模型）</span>
        <div>
          <el-button size="small" :loading="generating" type="primary" @click="regenerate">
            {{ review.ai_comment ? '重新生成' : '生成 AI 评论' }}
          </el-button>
          <el-button size="small" :disabled="!review.ai_comment_version" @click="openHistory">历史</el-button>
        </div>
      </div>
    </template>

    <div v-if="review.ai_comment">
      <p class="muted" v-if="review.ai_comment_time">
        生成时间：{{ review.ai_comment_time }}
        <span v-if="review.review_model_id"> · 模型#{{ review.review_model_id }}</span>
        · v{{ review.ai_comment_version }}
      </p>
      <el-descriptions :column="1" border size="small" class="mt8">
        <el-descriptions-item label="总体评价">{{ comment.summary || '-' }}</el-descriptions-item>
        <el-descriptions-item label="深度评估">
          <el-tag size="small">{{ comment.depth_assessment?.depth_level || '-' }}</el-tag>
          <span class="score">{{ comment.depth_assessment?.score ?? '' }}</span>
          <div class="muted">{{ comment.depth_assessment?.comment }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="亮点">
          <ul class="li"><li v-for="(s, i) in comment.strengths || []" :key="i">{{ s }}</li></ul>
        </el-descriptions-item>
        <el-descriptions-item label="不足">
          <ul class="li"><li v-for="(s, i) in comment.weaknesses || []" :key="i">{{ s }}</li></ul>
        </el-descriptions-item>
        <el-descriptions-item label="改进建议">
          <ul class="li"><li v-for="(s, i) in comment.suggestions || []" :key="i">{{ s }}</li></ul>
        </el-descriptions-item>
        <el-descriptions-item label="理论参照">
          <div v-for="(t, i) in comment.theory_reference || []" :key="i" class="muted">
            · {{ t.theory_name }}：{{ t.how_applied }}
          </div>
          <span v-if="!(comment.theory_reference && comment.theory_reference.length)">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="结论评论">{{ comment.conclusion || '-' }}</el-descriptions-item>
      </el-descriptions>
    </div>
    <el-empty v-else description="暂未生成 AI 评论，点击右上角生成（约30-60秒）" :image-size="50" />

    <el-dialog v-model="historyVisible" title="AI 评论历史版本" width="640px" append-to-body>
      <el-empty v-if="!history.length" description="暂无历史" />
      <el-timeline v-else>
        <el-timeline-item v-for="h in history" :key="h.version" :timestamp="h.generate_time" placement="top">
          <p class="bold">v{{ h.version }} · {{ h.scope }} <span v-if="h.model_id">· 模型#{{ h.model_id }}</span></p>
          <p class="muted">{{ h.ai_comment_text || h.ai_comment?.summary }}</p>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>
  </el-card>
</template>

<script setup name="AiCommentPanel">
import { ElMessage } from 'element-plus'
import { generateAiComment, listAiCommentHistory } from '@/api/learning/review'

const props = defineProps({
  recordId: { type: [Number, String, null], default: null },
  review: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['refresh'])

const generating = ref(false)
const historyVisible = ref(false)
const history = ref([])

const comment = computed(() => props.review?.ai_comment || {})

async function regenerate() {
  if (!props.recordId) return
  generating.value = true
  try {
    await generateAiComment(props.recordId, { scope: 'reflection' })
    ElMessage.success('AI 评论已生成')
    emit('refresh')
  } catch (e) {
    ElMessage.error(e?.message || '生成失败，请重试')
  } finally {
    generating.value = false
  }
}

async function openHistory() {
  history.value = []
  historyVisible.value = true
  try {
    const res = await listAiCommentHistory(props.recordId)
    history.value = res?.data || []
  } catch (e) {
    history.value = []
  }
}
</script>

<style scoped>
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.bold {
  font-weight: bold;
}
.muted {
  color: #909399;
  font-size: 12px;
}
.mt8 {
  margin-top: 8px;
}
.score {
  margin-left: 6px;
  color: #409eff;
}
.li {
  margin: 0;
  padding-left: 18px;
}
</style>
