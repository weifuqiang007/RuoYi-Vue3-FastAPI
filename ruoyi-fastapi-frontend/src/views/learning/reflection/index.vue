<template>
  <div>
    <DepthIndicator :depth-score="depthScore" :depth-level="depthLevel" class="mb8" />

    <el-row :gutter="16">
      <el-col :span="14">
        <ReflectionEditor v-model="content" @blur="handleBlurSave">
          <template #actions>
            <el-button :loading="saving" @click="save">保存</el-button>
            <el-button type="success" :loading="confirming" @click="confirm">确认并进入研究区</el-button>
          </template>
        </ReflectionEditor>
        <div class="mb8" />
        <DepthChart :history="depthHistory" />
      </el-col>

      <el-col :span="10">
        <AiQuestionPanel
          :reflection-id="reflectionId"
          :initial-questions="questions"
          @update:questions="(v) => (questions.value = normalizeArray(v))"
          @update:theories="(v) => (theories.value = normalizeArray(v))"
          @update:depth="handleDepthUpdate"
        />
        <div class="mb8" />
        <TheoryLinkage :theories="theories" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="LearningReflection">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { confirmReflection, getReflectionDepthHistory, getReflectionDetail, saveReflection } from '@/api/learning/reflection'
import { useAutoSave } from '@/views/learning/components/AutoSaveMixin'
import DepthIndicator from './components/DepthIndicator.vue'
import ReflectionEditor from './components/ReflectionEditor.vue'
import AiQuestionPanel from './components/AiQuestionPanel.vue'
import TheoryLinkage from './components/TheoryLinkage.vue'
import DepthChart from './components/DepthChart.vue'

const props = defineProps({
  recordId: { type: [String, Number], required: true },
  record: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['stage-updated'])

const reflectionId = ref(null)
const content = ref('')

const depthScore = ref(0)
const depthLevel = ref('')

const questions = ref([])
const theories = ref([])
const depthHistory = ref([])

const saving = ref(false)
const confirming = ref(false)

function normalizeArray(v) {
  if (!v) return []
  if (Array.isArray(v)) return v
  return [v]
}

async function loadDetail() {
  const res = await getReflectionDetail(props.recordId)
  const data = res.data || {}
  reflectionId.value = data.reflection_id ?? data.reflectionId ?? null
  content.value = data.content ?? ''
  depthScore.value = Number(data.depth_score ?? data.depthScore ?? 0)
  depthLevel.value = data.depth_level ?? data.depthLevel ?? ''
  questions.value = normalizeArray(data.questions ?? data.question_list ?? [])
  theories.value = normalizeArray(data.theories ?? data.linked_theories ?? data.linkedTheories ?? [])
  await loadDepthHistory()
}

async function loadDepthHistory() {
  if (!reflectionId.value) {
    depthHistory.value = []
    return
  }
  const res = await getReflectionDepthHistory(reflectionId.value)
  const data = res.data || []
  depthHistory.value = Array.isArray(data) ? data : []
}

async function save() {
  if (!content.value.trim()) {
    ElMessage.warning('请先填写反思内容')
    return
  }
  saving.value = true
  try {
    const res = await saveReflection({
      record_id: props.recordId,
      reflection_id: reflectionId.value,
      content: content.value
    })
    const data = res.data || {}
    reflectionId.value = reflectionId.value ?? data.reflection_id ?? data.reflectionId ?? null
    if (data.depth_score !== undefined) depthScore.value = Number(data.depth_score)
    if (data.depth_level) depthLevel.value = data.depth_level
    if (data.linked_theories || data.theories) theories.value = normalizeArray(data.linked_theories ?? data.theories)
    ElMessage.success('保存成功')
    emit('stage-updated')
    await loadDepthHistory()
  } finally {
    saving.value = false
  }
}

function handleDepthUpdate(payload) {
  if (!payload) return
  if (payload.depth_score !== undefined) depthScore.value = Number(payload.depth_score)
  if (payload.depth_level) depthLevel.value = payload.depth_level
}

async function confirm() {
  confirming.value = true
  try {
    await confirmReflection({ record_id: props.recordId, reflection_id: reflectionId.value })
    ElMessage.success('已确认')
    emit('stage-updated')
  } finally {
    confirming.value = false
  }
}

function handleBlurSave() {
  autoSave.scheduleDebouncedSave('blur')
}

const autoSave = useAutoSave({
  saveFn: () => save(),
  debounceMs: 800,
  intervalMs: 30000
})

watch(
  () => content.value,
  () => {
    autoSave.scheduleDebouncedSave('input')
  }
)

onMounted(() => {
  loadDetail()
  autoSave.startInterval()
})

onBeforeUnmount(() => {
  autoSave.dispose()
})
</script>
