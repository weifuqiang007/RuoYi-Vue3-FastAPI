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

      <el-divider content-position="left">各区知识库配置</el-divider>

      <el-row :gutter="14">
        <el-col :span="12">
          <el-form-item label="情境区KB">
            <el-select v-model="form.scenario_kb_ids" multiple filterable clearable style="width: 100%">
              <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="决策区KB">
            <el-select v-model="form.decision_kb_ids" multiple filterable clearable style="width: 100%">
              <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="14">
        <el-col :span="12">
          <el-form-item label="反思区KB">
            <el-select v-model="form.reflection_kb_ids" multiple filterable clearable style="width: 100%">
              <el-option v-for="kb in kbOptions" :key="kb.kb_id" :label="kb.kb_name" :value="kb.kb_id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="研究区KB">
            <el-select v-model="form.research_kb_ids" multiple filterable clearable style="width: 100%">
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
  deadline: ''
})

const rules = {
  task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }]
}

async function loadKbOptions() {
  const res = await listKnowledgeBase()
  kbOptions.value = res.data || []
}

function resetFormFromProps() {
  const d = props.data || {}
  form.task_id = d.task_id ?? d.taskId
  form.task_name = d.task_name ?? d.taskName ?? ''
  form.task_description = d.task_description ?? d.taskDescription ?? ''
  form.preset_scenario = d.preset_scenario ?? d.presetScenario ?? ''
  form.scenario_kb_ids = (d.scenario_kb_ids ?? d.scenarioKbIds ?? []).slice?.() || []
  form.decision_kb_ids = (d.decision_kb_ids ?? d.decisionKbIds ?? []).slice?.() || []
  form.reflection_kb_ids = (d.reflection_kb_ids ?? d.reflectionKbIds ?? []).slice?.() || []
  form.research_kb_ids = (d.research_kb_ids ?? d.researchKbIds ?? []).slice?.() || []
  form.deadline = d.deadline ?? ''
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
      deadline: form.deadline || null
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
      if (kbOptions.value.length === 0) {
        await loadKbOptions()
      }
      resetFormFromProps()
    }
  }
)
</script>

