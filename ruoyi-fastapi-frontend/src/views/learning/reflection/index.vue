<template>
  <div>
    <!-- 顶部：平均深度指示器 -->
    <DepthIndicator :depth-score="avgDepthScore" :depth-level="avgDepthLevel" class="mb8" />

    <!-- 按关键事件分 Tab -->
    <el-card shadow="never" class="mb8">
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane
          v-for="item in tabItems"
          :key="item.decisionId"
          :label="`关键事件 ${item.index + 1}：${truncate(item.keyEventDesc, 15)}`"
          :name="String(item.decisionId)"
        >
          <DecisionReflectionTab
            :ref="el => tabRefs[item.decisionId] = el"
            :decision-id="item.decisionId"
            :key-event-desc="item.keyEventDesc"
            :record-id="recordId"
            :reflection-data="item.reflectionData"
            @saved="onTabSaved"
            @guidance-generated="onTabGuidanceGenerated"
            @depth-loaded="onTabDepthLoaded"
          />
        </el-tab-pane>
      </el-tabs>
      <el-empty v-if="tabItems.length === 0" description="请先完成决策区（至少需要一条决策记录）" />
    </el-card>

    <!-- 底部：深度折线图 + 理论总览 + 确认按钮 -->
    <el-row :gutter="16">
      <el-col :span="14">
        <DepthChart :history="currentDepthHistory" />
      </el-col>
      <el-col :span="10">
        <TheoryLinkage :theories="aggregatedTheories" />
        <div class="mb8" />
        <el-card shadow="never">
          <el-button
            type="success"
            :loading="confirming"
            style="width: 100%"
            @click="confirm"
          >
            确认并进入研究区
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="LearningReflection">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getReflectionList, confirmReflection } from '@/api/learning/reflection'
import { listDecision } from '@/api/learning/decision'
import { advanceRecordStage, getRecordDetail } from '@/api/learning/record'
import DepthIndicator from './components/DepthIndicator.vue'
import DepthChart from './components/DepthChart.vue'
import TheoryLinkage from './components/TheoryLinkage.vue'
import DecisionReflectionTab from './components/DecisionReflectionTab.vue'

const props = defineProps({
  recordId: { type: [String, Number], required: true },
  record: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['stage-updated'])

const route = useRoute()
const router = useRouter()

const activeTab = ref('')
const tabItems = ref([])
const tabRefs = ref({})
const confirming = ref(false)

/** 每个 Tab 的最新状态（由子组件通过事件上报） */
const tabStates = ref({})

/** 平均深度 */
const avgDepthScore = computed(() => {
  const states = Object.values(tabStates.value)
  if (!states.length) return 0
  const sum = states.reduce((acc, s) => acc + (s.depthScore || 0), 0)
  return sum / states.length
})

const avgDepthLevel = computed(() => {
  const score = avgDepthScore.value
  if (score >= 0.71) return 'reflexive'
  if (score >= 0.41) return 'analytical'
  return 'descriptive'
})

const activeTabState = computed(() => {
  return tabStates.value[activeTab.value] || {}
})

const currentDepthHistory = computed(() => {
  return Array.isArray(activeTabState.value.depthHistory)
    ? activeTabState.value.depthHistory
    : []
})

const currentTheories = computed(() => {
  return Array.isArray(activeTabState.value.theories)
    ? activeTabState.value.theories
    : []
})

const aggregatedTheories = computed(() => {
  const allTheories = []
  const seen = new Map() // 用来去重和追踪来源
  
  Object.entries(tabStates.value).forEach(([decisionId, state]) => {
    const theories = Array.isArray(state.theories) ? state.theories : []
    const tabIndex = tabItems.value.findIndex(item => String(item.decisionId) === String(decisionId))
    const tabLabel = tabIndex >= 0 ? `关键事件 ${tabIndex + 1}` : ''
    
    theories.forEach(theory => {
      const key = theory.name || theory.theory_name || JSON.stringify(theory)
      if (!seen.has(key)) {
        seen.set(key, {
          ...theory,
          // 添加来源标注
          sources: [tabLabel]
        })
      } else {
        // 如果重复，添加到来源列表
        const existing = seen.get(key)
        if (tabLabel && !existing.sources.includes(tabLabel)) {
          existing.sources.push(tabLabel)
        }
      }
    })
  })
  
  return Array.from(seen.values())
})

function truncate(str, len) {
  if (!str) return '未命名'
  return str.length > len ? str.slice(0, len) + '...' : str
}

async function loadData() {
  // 1. 获取决策列表
  const decisionRes = await listDecision(props.recordId)
  const decisions = decisionRes.data || []

  // 2. 获取反思列表
  const reflectionRes = await getReflectionList(props.recordId)
  const reflections = reflectionRes.data || []

  // 3. 构建反射映射：decision_id -> reflection
  const reflectionMap = {}
  reflections.forEach(r => {
    if (r.decision_id) {
      reflectionMap[r.decision_id] = r
    }
  })

  // 4. 构建 Tab 项（使用决策记录中的 key_event_index，而非数组下标）
  tabItems.value = decisions.map((d) => ({
    decisionId: d.decision_id ?? d.decisionId,
    keyEventDesc: d.key_event_desc ?? d.keyEventDesc ?? '',
    index: d.key_event_index ?? d.keyEventIndex ?? 0,
    reflectionData: reflectionMap[d.decision_id ?? d.decisionId] || null,
  }))

  // 5. 初始化 tabStates
  const states = {}
  tabItems.value.forEach(item => {
    const r = item.reflectionData
    states[item.decisionId] = {
      depthScore: Number(r?.depth_score ?? r?.depthScore ?? 0),
      depthLevel: r?.depth_level ?? r?.depthLevel ?? '',
      depthHistory: [],
      theories: r?.linked_theories || r?.linkedTheories || [],
    }
  })
  tabStates.value = states

  // 6. 设置默认激活的 Tab
  if (tabItems.value.length > 0 && !activeTab.value) {
    activeTab.value = String(tabItems.value[0].decisionId)
  }
}

function onTabSaved({ decisionId, reflectionId, depthScore, depthLevel }) {
  if (!tabStates.value[decisionId]) return
  tabStates.value[decisionId].depthScore = depthScore
  tabStates.value[decisionId].depthLevel = depthLevel
  emit('stage-updated')
}

function onTabGuidanceGenerated({ decisionId, depthScore, depthLevel, theories }) {
  if (!tabStates.value[decisionId]) return
  tabStates.value[decisionId].depthScore = depthScore
  tabStates.value[decisionId].depthLevel = depthLevel
  tabStates.value[decisionId].theories = theories || []
}

/** 子组件加载/刷新深度历史后上报，填入 tabStates 供底部 DepthChart 聚合 */
function onTabDepthLoaded({ decisionId, depthHistory: history }) {
  if (!tabStates.value[decisionId]) return
  tabStates.value[decisionId].depthHistory = Array.isArray(history) ? history : []
}

async function confirm() {
  // 校验每个 Tab 都有反思内容
  const emptyTabs = tabItems.value.filter(item => {
    const ref = tabRefs.value[item.decisionId]
    return !ref || !ref.content || !ref.content.trim()
  })
  if (emptyTabs.length > 0) {
    const names = emptyTabs.map(t => truncate(t.keyEventDesc, 20))
    ElMessage.warning(`以下关键事件尚未反思：${names.join('、')}`)
    return
  }

  confirming.value = true
  try {
    // 保存当前 Tab
    const currentRef = tabRefs.value[activeTab.value]
    if (currentRef && currentRef.content?.trim()) {
      await currentRef.save()
    }

    // 判断当前记录状态
    const currentStage = props.record?.current_stage ?? props.record?.currentStage
    const isOngoing = !['submitted', 'completed'].includes(String(currentStage))

    if (isOngoing) {
      await confirmReflection({ record_id: props.recordId })
      await advanceRecordStage(props.recordId)
    }

    router.replace({ query: { ...route.query, stage: 'research' } })
    ElMessage.success(isOngoing ? '已保存并推进到研究生成区' : '已跳转到研究生成区')
    emit('stage-updated')
  } finally {
    confirming.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.mb8 {
  margin-bottom: 8px;
}
</style>
