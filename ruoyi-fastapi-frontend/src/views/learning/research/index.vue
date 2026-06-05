<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="12">
        <MaterialSummary :text="materialSummary">
          <template #actions>
            <el-button size="small" :loading="initializing" @click="init">重新汇总</el-button>
          </template>
        </MaterialSummary>
        <div class="mb8" />
        <QuestionSelector v-model="selectedQuestion" :questions="candidateQuestions">
          <template #actions>
            <el-button size="small" type="primary" :loading="questionLoading" :disabled="!researchId" @click="genQuestions">
              生成候选问题
            </el-button>
          </template>
        </QuestionSelector>
        <div class="mb8" />
        <FrameworkEditor v-model="framework">
          <template #actions>
            <el-button
              size="small"
              type="primary"
              :loading="frameworkLoading"
              :disabled="!researchId || !selectedQuestion"
              @click="genFramework"
            >
              生成论文框架
            </el-button>
          </template>
        </FrameworkEditor>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never" class="mb8">
          <template #header>
            <div class="header">
              <span>章节撰写</span>
              <div class="actions">
                <el-button type="success" :loading="submitting" :disabled="!researchId" @click="submitAll">提交研究成果</el-button>
              </div>
            </div>
          </template>

          <div v-if="chapters.length === 0" class="empty">暂无章节</div>
          <el-tabs v-else v-model="activeTab">
            <el-tab-pane
              v-for="c in chapters"
              :key="c.chapter_id"
              :label="`${c.chapter_index}. ${c.chapter_title || '章节'}`"
              :name="String(c.chapter_id)"
            >
              <ChapterEditor
                v-model="c.content"
                :title="`${c.chapter_index}. ${c.chapter_title || '章节'}`"
                :ai-suggestion="c.ai_suggestion"
                :saving="savingChapterId === c.chapter_id"
                :drafting="draftingChapterId === c.chapter_id"
                @save="() => saveChapter(c)"
                @draft="() => draftChapter(c)"
              />
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <div class="header">
              <span>参考文献推荐</span>
              <div class="actions">
                <el-button size="small" type="primary" :loading="refLoading" :disabled="!researchId" @click="genReferences">
                  推荐文献
                </el-button>
              </div>
            </div>
          </template>
          <div v-if="references.length === 0" class="empty">暂无</div>
          <el-table v-else :data="references" size="small">
            <el-table-column label="文献" min-width="220">
              <template #default="scope">{{ formatRef(scope.row) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="LearningResearch">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  draftResearchChapter,
  generateResearchFramework,
  generateResearchQuestions,
  initResearch,
  recommendResearchReferences,
  saveResearchChapter,
  submitResearch
} from '@/api/learning/research'
import MaterialSummary from './components/MaterialSummary.vue'
import QuestionSelector from './components/QuestionSelector.vue'
import FrameworkEditor from './components/FrameworkEditor.vue'
import ChapterEditor from './components/ChapterEditor.vue'

const props = defineProps({
  recordId: { type: [String, Number], required: true },
  record: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['stage-updated'])

const researchId = ref(null)
const materialSummary = ref('')
const candidateQuestions = ref([])
const selectedQuestion = ref('')
const framework = ref(null)
const references = ref([])

const chapters = ref([])
const activeTab = ref('')

const initializing = ref(false)
const questionLoading = ref(false)
const frameworkLoading = ref(false)
const savingChapterId = ref(null)
const draftingChapterId = ref(null)
const refLoading = ref(false)
const submitting = ref(false)

function normalizeChapter(row) {
  return {
    chapter_id: row.chapter_id ?? row.chapterId,
    chapter_index: row.chapter_index ?? row.chapterIndex ?? 1,
    chapter_title: row.chapter_title ?? row.chapterTitle ?? '',
    content: row.content ?? '',
    ai_suggestion: row.ai_suggestion ?? row.aiSuggestion ?? ''
  }
}

async function init() {
  initializing.value = true
  try {
    const res = await initResearch(props.recordId)
    const data = res.data || {}
    researchId.value = data.research_id ?? data.researchId ?? researchId.value
    materialSummary.value = data.material_summary ?? data.materialSummary ?? materialSummary.value
    candidateQuestions.value = data.candidate_questions ?? data.candidateQuestions ?? candidateQuestions.value
    selectedQuestion.value = data.selected_question ?? data.selectedQuestion ?? selectedQuestion.value
    framework.value = data.framework ?? framework.value
    references.value = data.references ?? references.value
    const rawChapters = data.chapters ?? []
    chapters.value = Array.isArray(rawChapters) ? rawChapters.map(normalizeChapter) : []
    if (chapters.value.length) activeTab.value = String(chapters.value[0].chapter_id)
    emit('stage-updated')
  } finally {
    initializing.value = false
  }
}

async function genQuestions() {
  if (!researchId.value) return
  questionLoading.value = true
  try {
    const res = await generateResearchQuestions({ research_id: researchId.value })
    const data = res.data || {}
    candidateQuestions.value = data.candidate_questions ?? data.questions ?? data ?? []
    if (Array.isArray(candidateQuestions.value) && candidateQuestions.value.length && !selectedQuestion.value) {
      selectedQuestion.value = typeof candidateQuestions.value[0] === 'string' ? candidateQuestions.value[0] : ''
    }
  } finally {
    questionLoading.value = false
  }
}

async function genFramework() {
  if (!researchId.value) return
  if (!selectedQuestion.value) {
    ElMessage.warning('请先选择一个研究问题')
    return
  }
  frameworkLoading.value = true
  try {
    const res = await generateResearchFramework({ research_id: researchId.value, selected_question: selectedQuestion.value })
    const data = res.data || {}
    framework.value = data.framework ?? data
    const rawChapters = data.chapters ?? []
    if (Array.isArray(rawChapters) && rawChapters.length) {
      chapters.value = rawChapters.map(normalizeChapter)
      activeTab.value = String(chapters.value[0].chapter_id)
    }
  } finally {
    frameworkLoading.value = false
  }
}

async function saveChapter(chapter) {
  if (!researchId.value || !chapter?.chapter_id) return
  savingChapterId.value = chapter.chapter_id
  try {
    await saveResearchChapter({
      research_id: researchId.value,
      chapter_id: chapter.chapter_id,
      content: chapter.content
    })
    ElMessage.success('保存成功')
  } finally {
    savingChapterId.value = null
  }
}

async function draftChapter(chapter) {
  if (!researchId.value || !chapter?.chapter_id) return
  draftingChapterId.value = chapter.chapter_id
  try {
    const res = await draftResearchChapter({
      research_id: researchId.value,
      chapter_id: chapter.chapter_id,
      content: chapter.content
    })
    const data = res.data || {}
    if (data.content) chapter.content = data.content
    if (data.ai_suggestion) chapter.ai_suggestion = data.ai_suggestion
    ElMessage.success('生成完成')
  } finally {
    draftingChapterId.value = null
  }
}

async function genReferences() {
  if (!researchId.value) return
  refLoading.value = true
  try {
    const res = await recommendResearchReferences({ research_id: researchId.value })
    const data = res.data || {}
    references.value = data.references ?? data ?? []
  } finally {
    refLoading.value = false
  }
}

async function submitAll() {
  if (!researchId.value) return
  submitting.value = true
  try {
    await submitResearch({ research_id: researchId.value })
    ElMessage.success('已提交')
    emit('stage-updated')
  } finally {
    submitting.value = false
  }
}

function formatRef(r) {
  if (typeof r === 'string') return r
  if (r?.title) return r.title
  if (r?.citation) return r.citation
  return JSON.stringify(r)
}

onMounted(() => {
  init()
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
</style>

