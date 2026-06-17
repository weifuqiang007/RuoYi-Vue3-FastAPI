<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="12">
        <MaterialSummary v-model="materialSummary">
          <template #actions>
            <el-button size="small" :loading="initializing" @click="init(true)">重新汇总</el-button>
          </template>
        </MaterialSummary>
        <div class="mb8" />
        <QuestionSelector v-model="selectedQuestion" :questions="candidateQuestions" :stream-text="questionStreamText">
          <template #actions>
            <el-button size="small" type="primary" :loading="questionLoading" :disabled="!researchId" @click="genQuestions">
              生成候选问题
            </el-button>
          </template>
        </QuestionSelector>
        <div class="mb8" />
        <FrameworkEditor v-model="framework" :stream-text="frameworkStreamText">
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
                <el-button :loading="savingAll" :disabled="!researchId" @click="saveAll">保存</el-button>
                <el-button :disabled="!researchId" @click="downloadMarkdown">下载Markdown</el-button>
                <el-button type="success" :loading="submitting" :disabled="!researchId" @click="submitAll">提交研究成果</el-button>
              </div>
            </div>
          </template>

          <div v-if="chapters.length === 0" class="empty">暂无章节（请先生成论文框架）</div>
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
                :draft-stream-text="draftingChapterId === c.chapter_id ? chapterDraftStreamText : ''"
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
          <!-- 流式生成中 -->
          <div v-if="refStreamText && references.length === 0" class="stream-preview">{{ refStreamText }}<span class="cursor">|</span></div>
          <div v-else-if="references.length === 0" class="empty">暂无</div>
          <el-table v-else :data="references" size="small">
            <el-table-column label="文献" min-width="220">
              <template #default="scope">{{ formatRef(scope.row) }}</template>
            </el-table-column>
            <el-table-column v-if="references.some(r => r.relevance)" label="关联说明" min-width="180">
              <template #default="scope">{{ scope.row.relevance || '' }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="LearningResearch">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  draftResearchChapter,
  draftResearchChapterStream,
  generateResearchFramework,
  generateResearchFrameworkStream,
  generateResearchQuestions,
  generateResearchQuestionsStream,
  initResearch,
  recommendResearchReferences,
  recommendResearchReferencesStream,
  saveResearch,
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
const questionStreamText = ref('')
const selectedQuestion = ref('')
const framework = ref(null)
const frameworkStreamText = ref('')
const references = ref([])
const refStreamText = ref('')
const chapterDraftStreamText = ref('')

const chapters = ref([])
const activeTab = ref('')

const initializing = ref(false)
const questionLoading = ref(false)
const questionAbortController = ref(null)
const frameworkLoading = ref(false)
const frameworkAbortController = ref(null)
const savingChapterId = ref(null)
const draftingChapterId = ref(null)
const chapterAbortController = ref(null)
const refLoading = ref(false)
const refAbortController = ref(null)
const savingAll = ref(false)
const submitting = ref(false)

function normalizeChapter(row) {
  const suggestion = row.ai_suggestion ?? row.aiSuggestion ?? ''
  const content = row.content ?? suggestion
  return {
    chapter_id: row.chapter_id ?? row.chapterId,
    chapter_index: row.chapter_index ?? row.chapterIndex ?? 1,
    chapter_title: row.chapter_title ?? row.chapterTitle ?? '',
    content,
    ai_suggestion: suggestion || content
  }
}

async function init(force = false) {
  initializing.value = true
  try {
    const res = await initResearch(props.recordId, force)
    const data = res.data || {}
    researchId.value = data.research_id ?? data.researchId ?? researchId.value
    materialSummary.value = data.material_summary ?? data.materialSummary ?? materialSummary.value
    if (force) {
      // 重新汇总：强制用后端最新数据刷新各字段
      candidateQuestions.value = data.candidate_questions ?? data.candidateQuestions ?? []
      selectedQuestion.value = data.selected_question ?? data.selectedQuestion ?? ''
      framework.value = data.framework ?? null
      references.value = data.references ?? data.ref_literature ?? []
      const rawChapters = data.chapters ?? []
      chapters.value = Array.isArray(rawChapters) ? rawChapters.map(normalizeChapter) : []
      if (chapters.value.length) activeTab.value = String(chapters.value[0].chapter_id)
      ElMessage.success('已重新汇总前三区材料')
    } else {
      candidateQuestions.value = data.candidate_questions ?? data.candidateQuestions ?? candidateQuestions.value
      selectedQuestion.value = data.selected_question ?? data.selectedQuestion ?? selectedQuestion.value
      framework.value = data.framework ?? framework.value
      references.value = data.references ?? data.ref_literature ?? references.value
      const rawChapters = data.chapters ?? []
      chapters.value = Array.isArray(rawChapters) ? rawChapters.map(normalizeChapter) : []
      if (chapters.value.length) activeTab.value = String(chapters.value[0].chapter_id)
    }
    emit('stage-updated')
  } finally {
    initializing.value = false
  }
}

// ── 保存全部 ──

async function saveAll() {
  if (!researchId.value) return
  savingAll.value = true
  try {
    // 一次性保存：研究问题 + 材料汇总 + 所有章节内容
    await saveResearch({
      research_id: researchId.value,
      selected_question: selectedQuestion.value || null,
      material_summary: materialSummary.value || null,
      chapters: chapters.value.map(c => ({
        chapter_index: c.chapter_index,
        content: c.content ?? '',
      })),
    })
    syncChapterSuggestions()
    ElMessage.success('保存成功')
  } catch (err) {
    ElMessage.error('保存失败：' + (err?.message || '未知错误'))
  } finally {
    savingAll.value = false
  }
}

// ── 生成候选问题（流式） ──

async function genQuestions() {
  if (!researchId.value) return
  questionLoading.value = true
  questionStreamText.value = ''
  candidateQuestions.value = []
  questionAbortController.value = new AbortController()
  try {
    await generateResearchQuestionsStream(
      { research_id: researchId.value },
      {
        onStatus: (message) => {
          if (!questionStreamText.value && message) questionStreamText.value = `${message}\n\n`
        },
        onContent: (content) => {
          questionStreamText.value += content || ''
        },
        onResult: (data) => {
          candidateQuestions.value = data?.candidate_questions ?? data?.questions ?? []
        },
        onError: (message) => {
          throw new Error(message || '生成失败')
        }
      },
      questionAbortController.value.signal
    )
    if (Array.isArray(candidateQuestions.value) && candidateQuestions.value.length && !selectedQuestion.value) {
      selectedQuestion.value = formatQuestionValue(candidateQuestions.value[0])
    }
    questionStreamText.value = ''
  } catch (err) {
    if (err?.name !== 'AbortError') {
      ElMessage.error('生成候选问题失败：' + (err?.message || '未知错误'))
      try {
        const res = await generateResearchQuestions({ research_id: researchId.value })
        const data = res.data || {}
        candidateQuestions.value = data.candidate_questions ?? data.questions ?? data ?? []
        if (Array.isArray(candidateQuestions.value) && candidateQuestions.value.length && !selectedQuestion.value) {
          selectedQuestion.value = formatQuestionValue(candidateQuestions.value[0])
        }
        questionStreamText.value = ''
      } catch {
      }
    }
  } finally {
    questionLoading.value = false
    questionAbortController.value = null
  }
}

// ── 生成论文框架（流式） ──

async function genFramework() {
  if (!researchId.value) return
  if (!selectedQuestion.value) {
    ElMessage.warning('请先选择一个研究问题')
    return
  }
  frameworkLoading.value = true
  frameworkStreamText.value = ''
  frameworkAbortController.value = new AbortController()
  try {
    await generateResearchFrameworkStream(
      { research_id: researchId.value, selected_question: selectedQuestion.value },
      {
        onStatus: (message) => {
          if (!frameworkStreamText.value && message) frameworkStreamText.value = `${message}\n\n`
        },
        onContent: (content) => {
          frameworkStreamText.value += content || ''
        },
        onResult: (data) => {
          framework.value = data?.framework ?? framework.value
          const rawChapters = data?.chapters ?? []
          if (Array.isArray(rawChapters) && rawChapters.length) {
            chapters.value = rawChapters.map(normalizeChapter)
            activeTab.value = String(chapters.value[0].chapter_id)
          }
          frameworkStreamText.value = ''
        },
        onError: (message) => {
          throw new Error(message || '生成失败')
        }
      },
      frameworkAbortController.value.signal
    )
  } catch (err) {
    if (err?.name !== 'AbortError') {
      ElMessage.error('生成论文框架失败：' + (err?.message || '未知错误'))
      // fallback 非流式
      try {
        const res = await generateResearchFramework({ research_id: researchId.value, selected_question: selectedQuestion.value })
        const data = res.data || {}
        framework.value = data.framework ?? data
        const rawChapters = data.chapters ?? []
        if (Array.isArray(rawChapters) && rawChapters.length) {
          chapters.value = rawChapters.map(normalizeChapter)
          activeTab.value = String(chapters.value[0].chapter_id)
        }
        frameworkStreamText.value = ''
      } catch {
      }
    }
  } finally {
    frameworkLoading.value = false
    frameworkAbortController.value = null
  }
}

// ── 保存章节 ──

async function saveChapter(chapter) {
  if (!researchId.value || !chapter?.chapter_id) return
  savingChapterId.value = chapter.chapter_id
  try {
    await saveResearchChapter({
      research_id: researchId.value,
      chapter_index: chapter.chapter_index,
      content: chapter.content
    })
    chapter.ai_suggestion = chapter.content || ''
    ElMessage.success('保存成功')
  } finally {
    savingChapterId.value = null
  }
}

// ── AI 辅助撰写章节（流式） ──

async function draftChapter(chapter) {
  if (!researchId.value) return
  draftingChapterId.value = chapter.chapter_id
  chapterDraftStreamText.value = ''
  chapter.content = ''  // 清空编辑框，准备接收 AI 生成内容
  chapterAbortController.value = new AbortController()
  try {
    await draftResearchChapterStream(
      { research_id: researchId.value, chapter_index: chapter.chapter_index },
      {
        onStatus: () => {},
        onContent: (content) => {
          chapterDraftStreamText.value += content || ''
          chapter.content += content || ''  // 实时回填到编辑框
        },
        onResult: (data) => {
          const draft = data?.ai_suggestion ?? chapterDraftStreamText.value
          chapter.ai_suggestion = draft
          chapter.content = draft  // 最终确认回填
          chapterDraftStreamText.value = ''
        },
        onError: (message) => {
          throw new Error(message || '撰写失败')
        }
      },
      chapterAbortController.value.signal
    )
  } catch (err) {
    if (err?.name !== 'AbortError') {
      ElMessage.error('AI 辅助撰写失败：' + (err?.message || '未知错误'))
      // fallback 非流式
      try {
        const res = await draftResearchChapter({
          research_id: researchId.value,
          chapter_index: chapter.chapter_index
        })
        const data = res.data || {}
        const draft = data.content || data.ai_suggestion || ''
        if (draft) {
          chapter.content = draft
          chapter.ai_suggestion = draft
        }
        chapterDraftStreamText.value = ''
      } catch {
      }
    }
  } finally {
    draftingChapterId.value = null
    chapterAbortController.value = null
  }
}

// ── 推荐参考文献（流式） ──

async function genReferences() {
  if (!researchId.value) return
  refLoading.value = true
  refStreamText.value = ''
  references.value = []
  refAbortController.value = new AbortController()
  try {
    await recommendResearchReferencesStream(
      { research_id: researchId.value },
      {
        onStatus: (message) => {
          if (!refStreamText.value && message) refStreamText.value = `${message}\n\n`
        },
        onContent: (content) => {
          refStreamText.value += content || ''
        },
        onResult: (data) => {
          references.value = data?.references ?? []
          refStreamText.value = ''
        },
        onError: (message) => {
          throw new Error(message || '推荐失败')
        }
      },
      refAbortController.value.signal
    )
  } catch (err) {
    if (err?.name !== 'AbortError') {
      ElMessage.error('文献推荐失败：' + (err?.message || '未知错误'))
      // fallback 非流式
      try {
        const res = await recommendResearchReferences({ research_id: researchId.value })
        const data = res.data || {}
        references.value = data.references ?? data ?? []
        refStreamText.value = ''
      } catch {
      }
    }
  } finally {
    refLoading.value = false
    refAbortController.value = null
  }
}

// ── 提交 ──

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

// ── 工具函数 ──

function formatRef(r) {
  if (typeof r === 'string') return r
  if (r?.citation) return r.citation
  if (r?.title) return r.title
  return JSON.stringify(r)
}

function formatQuestionValue(q) {
  if (typeof q === 'string') return q
  if (q?.question) return q.question
  if (q?.content) return q.content
  return q ? JSON.stringify(q) : ''
}

function syncChapterSuggestions() {
  chapters.value.forEach((chapter) => {
    chapter.ai_suggestion = chapter.content || ''
  })
}

function downloadMarkdown() {
  const markdown = buildResearchMarkdown()
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `research-${props.recordId || researchId.value}.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function buildResearchMarkdown() {
  const parts = ['# 研究生成区成果', '']

  if (selectedQuestion.value) {
    parts.push('## 研究问题', '', selectedQuestion.value, '')
  }

  parts.push('## 论文框架', '')
  const frameworkItems = normalizeFrameworkItems(framework.value)
  if (frameworkItems.length) {
    frameworkItems.forEach((item, index) => {
      const title = item.title || item.name || `章节${item.index || index + 1}`
      const desc = item.description || item.desc || item.content || ''
      parts.push(`${item.index || index + 1}. ${title}`)
      if (desc) parts.push(`   ${desc}`)
    })
  } else {
    parts.push('暂无')
  }
  parts.push('')

  parts.push('## 章节撰写', '')
  if (chapters.value.length) {
    chapters.value
      .slice()
      .sort((a, b) => Number(a.chapter_index || 0) - Number(b.chapter_index || 0))
      .forEach((chapter) => {
        parts.push(`### ${chapter.chapter_index}. ${chapter.chapter_title || '章节'}`, '')
        parts.push(chapter.content || '暂无内容', '')
      })
  } else {
    parts.push('暂无', '')
  }

  parts.push('## 参考文献', '')
  if (references.value.length) {
    references.value.forEach((ref, index) => {
      parts.push(`${index + 1}. ${formatRef(ref)}`)
      if (ref && typeof ref === 'object' && ref.relevance) {
        parts.push(`   ${ref.relevance}`)
      }
    })
  } else {
    parts.push('暂无')
  }

  return `${parts.join('\n')}\n`
}

function normalizeFrameworkItems(value) {
  if (!value) return []
  if (Array.isArray(value)) return value
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }
  return []
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
.stream-preview {
  min-height: 80px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
  color: #303133;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.cursor {
  animation: blink 1s infinite;
  color: #409eff;
  font-weight: bold;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
