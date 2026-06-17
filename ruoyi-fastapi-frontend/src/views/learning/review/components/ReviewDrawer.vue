<template>
  <el-drawer
    :model-value="modelValue"
    @update:model-value="v => emit('update:modelValue', v)"
    title="反思批阅"
    size="86%"
    :destroy-on-close="true"
  >
    <div v-loading="loading">
      <el-descriptions :column="4" border class="mb8">
        <el-descriptions-item label="学生">{{ detail.record?.student_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="课题">{{ detail.record?.task_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="班级">{{ detail.record?.class_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ detail.record?.submit_time || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-row :gutter="12">
        <el-col :span="14">
          <StudentWorkPanel
            :scenario="detail.scenario || {}"
            :decisions="detail.decisions || []"
            :reflections="detail.reflections || []"
            :research="detail.research || {}"
          />
        </el-col>
        <el-col :span="10">
          <AiCommentPanel :record-id="recordId" :review="detail.review || {}" @refresh="loadDetail" />
          <TeacherCommentForm :record-id="recordId" :review="detail.review || {}" class="mt12" @refresh="loadDetail" />
        </el-col>
      </el-row>
    </div>
  </el-drawer>
</template>

<script setup name="ReviewDrawer">
import { getReviewDetail } from '@/api/learning/review'
import StudentWorkPanel from './StudentWorkPanel.vue'
import AiCommentPanel from './AiCommentPanel.vue'
import TeacherCommentForm from './TeacherCommentForm.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  recordId: { type: [Number, String, null], default: null }
})
const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const detail = ref({})

function loadDetail() {
  if (!props.recordId) return
  loading.value = true
  getReviewDetail(props.recordId)
    .then(res => {
      detail.value = res?.data ?? {}
    })
    .finally(() => {
      loading.value = false
    })
}

watch(
  () => [props.modelValue, props.recordId],
  ([visible]) => {
    if (visible && props.recordId) loadDetail()
  }
)
</script>

<style scoped>
.mb8 {
  margin-bottom: 12px;
}
.mt12 {
  margin-top: 12px;
}
</style>
