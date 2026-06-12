<template>
  <el-dialog :title="title" v-model="visible" width="760px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
      <el-row :gutter="14">
        <el-col :span="12">
          <el-form-item label="任务名称" prop="task_name">
            <el-input v-model="form.task_name" placeholder="请输入任务名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="截止时间">
            <el-date-picker
              v-model="form.deadline"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="可不填"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="任务描述">
        <el-input v-model="form.task_description" type="textarea" :rows="3" placeholder="可不填" />
      </el-form-item>

      <el-form-item label="预设情境">
        <el-input v-model="form.preset_scenario" type="textarea" :rows="4" placeholder="可不填（学生可自行填写）" />
      </el-form-item>

      <el-form-item label="分配班级">
        <el-select
          v-model="form.dept_ids"
          multiple
          filterable
          clearable
          placeholder="可选择多个班级"
          style="width: 100%"
        >
          <el-option v-for="d in deptOptions" :key="d.deptId" :label="d.deptName" :value="d.deptId" />
        </el-select>
      </el-form-item>

      <el-divider content-position="left">各区知识库配置</el-divider>

      <el-row :gutter="14">
        <el-col :span="12">
          <el-form-item label="情境区KB">
            <el-select
              v-model="form.scenario_kb_ids"
              multiple
              filterable
              clearable
              style="width: 100%"
              :loading="kbLoading"
              @visible-change="handleKbVisibleChange"
            >
              <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="决策区KB">
            <el-select
              v-model="form.decision_kb_ids"
              multiple
              filterable
              clearable
              style="width: 100%"
              :loading="kbLoading"
              @visible-change="handleKbVisibleChange"
            >
              <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="14">
        <el-col :span="12">
          <el-form-item label="反思区KB">
            <el-select
              v-model="form.reflection_kb_ids"
              multiple
              filterable
              clearable
              style="width: 100%"
              :loading="kbLoading"
              @visible-change="handleKbVisibleChange"
            >
              <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="研究区KB">
            <el-select
              v-model="form.research_kb_ids"
              multiple
              filterable
              clearable
              style="width: 100%"
              :loading="kbLoading"
              @visible-change="handleKbVisibleChange"
            >
              <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取 消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">确 定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listKnowledgeBase } from '@/api/rag/knowledgeBase'
import { listDept } from '@/api/system/dept'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  data: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const title = computed(() => (props.data?.task_id ? '编辑任务' : '创建任务'))

const kbOptions = ref([])
const kbLoading = ref(false)
const kbLoaded = ref(false)
const deptOptions = ref([])
const deptLoaded = ref(false)
const formRef = ref()
const submitting = ref(false)

const form = reactive({
  task_id: undefined,
  task_name: '',
  task_description: '',
  preset_scenario: '',
  scenario_kb_ids: [],
  decision_kb_ids: [],
  reflection_kb_ids: [],
  research_kb_ids: [],
  deadline: '',
  dept_ids: []
})

const rules = {
  task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }]
}

async function loadKbOptions() {
  if (kbLoading.value) return
  kbLoading.value = true
  try {
    const res = await listKnowledgeBase()
    const data = res?.data
    const rows = Array.isArray(data) ? data : Array.isArray(data?.rows) ? data.rows : []
    kbOptions.value = rows.map(normalizeKbOption)
    kbLoaded.value = true
  } catch (e) {
    kbOptions.value = []
    kbLoaded.value = false
    ElMessage.error(e?.message || '获取知识库列表失败')
  } finally {
    kbLoading.value = false
  }
}

function normalizeKbOption(kb) {
  const rawId = kb?.kb_id ?? kb?.kbId
  return {
    ...kb,
    kb_id: normalizeKbId(rawId),
    kb_name: kb?.kb_name ?? kb?.kbName ?? String(rawId ?? '')
  }
}

function normalizeKbId(id) {
  if (id === null || id === undefined || id === '') return id
  const n = Number(id)
  return Number.isNaN(n) ? id : n
}

function normalizeIdList(value) {
  if (Array.isArray(value)) return value.map(normalizeKbId).filter(id => id !== null && id !== undefined && id !== '')
  if (typeof value === 'string') {
    const text = value.trim()
    if (!text) return []
    try {
      const parsed = JSON.parse(text)
      if (Array.isArray(parsed)) return normalizeIdList(parsed)
    } catch (e) {
      // Ignore non-JSON strings and fall back to comma separated ids.
    }
    return text.split(',').map(item => normalizeKbId(item.trim())).filter(id => id !== null && id !== undefined && id !== '')
  }
  return value === null || value === undefined ? [] : [normalizeKbId(value)]
}

async function loadDeptOptions() {
  if (deptLoaded.value) return
  try {
    const res = await listDept()
    deptOptions.value = res.data || []
    deptLoaded.value = true
  } catch (e) {
    deptOptions.value = []
  }
}

async function ensureKbOptions() {
  if (kbLoaded.value && kbOptions.value.length > 0) return
  await loadKbOptions()
}

async function handleKbVisibleChange(v) {
  if (v) {
    await ensureKbOptions()
  }
}

function resetFormFromProps() {
  const d = props.data || {}
  form.task_id = d.task_id ?? d.taskId
  form.task_name = d.task_name ?? d.taskName ?? ''
  form.task_description = d.task_description ?? d.taskDescription ?? ''
  form.preset_scenario = d.preset_scenario ?? d.presetScenario ?? ''
  form.scenario_kb_ids = normalizeIdList(d.scenario_kb_ids ?? d.scenarioKbIds)
  form.decision_kb_ids = normalizeIdList(d.decision_kb_ids ?? d.decisionKbIds)
  form.reflection_kb_ids = normalizeIdList(d.reflection_kb_ids ?? d.reflectionKbIds)
  form.research_kb_ids = normalizeIdList(d.research_kb_ids ?? d.researchKbIds)
  form.deadline = d.deadline ?? ''
  // 回显已分配的班级：从 assigned_classes 中提取 dept_id 列表
  const ac = d.assigned_classes ?? d.assignedClasses ?? []
  form.dept_ids = Array.isArray(ac) ? ac.map(c => c.dept_id ?? c.deptId) : []
  formRef.value?.clearValidate?.()
}

async function submit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    emit('success', {
      task_id: form.task_id,
      task_name: form.task_name,
      task_description: form.task_description,
      preset_scenario: form.preset_scenario,
      scenario_kb_ids: form.scenario_kb_ids,
      decision_kb_ids: form.decision_kb_ids,
      reflection_kb_ids: form.reflection_kb_ids,
      research_kb_ids: form.research_kb_ids,
      deadline: form.deadline || null,
      dept_ids: form.dept_ids
    })
    visible.value = false
  } catch (e) {
    ElMessage.error(e?.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

watch(
  () => visible.value,
  async (v) => {
    if (v) {
      await Promise.all([ensureKbOptions(), loadDeptOptions()])
      resetFormFromProps()
    }
  }
)
</script>
