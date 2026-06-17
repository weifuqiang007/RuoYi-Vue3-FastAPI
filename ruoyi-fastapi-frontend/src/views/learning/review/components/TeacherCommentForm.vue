<template>
  <el-card>
    <template #header><span class="bold">老师点评（针对学生结论）</span></template>
    <el-form label-width="92px" :model="form">
      <el-form-item label="反思评分">
        <el-input-number v-model="form.reflection_score" :min="0" :max="100" :precision="1" controls-position="right" />
        <span class="muted ml">0-100</span>
      </el-form-item>
      <el-form-item label="反思点评">
        <el-input
          v-model="form.teacher_comment"
          type="textarea"
          :rows="3"
          placeholder="针对学生反思结论的点评（提交时必填）"
        />
      </el-form-item>
      <el-form-item label="总评">
        <el-input v-model="form.overall_comment" type="textarea" :rows="2" placeholder="可选" />
      </el-form-item>
      <el-form-item label="对AI评论">
        <el-input
          v-model="form.ai_comment_feedback"
          type="textarea"
          :rows="2"
          placeholder="对AI评论的看法（认同/补充/纠正），可选"
        />
      </el-form-item>
      <el-form-item>
        <el-button :loading="saving && mode === 'draft'" @click="save('draft')">保存草稿</el-button>
        <el-button type="primary" :loading="saving && mode === 'submit'" @click="save('submit')">提交点评</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup name="TeacherCommentForm">
import { ElMessage } from 'element-plus'
import { submitReviewComment } from '@/api/learning/review'

const props = defineProps({
  recordId: { type: [Number, String, null], default: null },
  review: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['refresh'])

const saving = ref(false)
const mode = ref('submit')
const form = reactive({
  reflection_score: null,
  teacher_comment: '',
  overall_comment: '',
  ai_comment_feedback: ''
})

watch(
  () => props.review,
  (v) => {
    const r = v || {}
    form.reflection_score = r.reflection_score ?? null
    form.teacher_comment = r.teacher_comment || ''
    form.overall_comment = r.overall_comment || ''
    form.ai_comment_feedback = r.ai_comment_feedback || ''
  },
  { immediate: true }
)

async function save(m) {
  if (!props.recordId) return
  mode.value = m
  if (m === 'submit' && !(form.teacher_comment && form.teacher_comment.trim())) {
    ElMessage.warning('提交点评时必须填写针对反思结论的点评')
    return
  }
  saving.value = true
  try {
    await submitReviewComment(props.recordId, {
      reflection_score: form.reflection_score,
      teacher_comment: form.teacher_comment,
      overall_comment: form.overall_comment,
      ai_comment_feedback: form.ai_comment_feedback,
      submit: m === 'submit'
    })
    ElMessage.success(m === 'submit' ? '点评已提交' : '草稿已保存')
    emit('refresh')
  } catch (e) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.bold {
  font-weight: bold;
}
.muted {
  color: #909399;
  font-size: 12px;
}
.ml {
  margin-left: 8px;
}
</style>
