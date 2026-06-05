<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>决策记录</span>
        <div class="actions">
          <slot name="actions" />
        </div>
      </div>
    </template>

    <el-form :model="form" label-width="110px">
      <el-form-item label="关键事件">
        <el-select v-model="form.key_event_index" placeholder="请选择关键事件" style="width: 100%">
          <el-option
            v-for="(e, idx) in keyEvents"
            :key="idx"
            :label="`事件 ${idx + 1}`"
            :value="idx"
          />
        </el-select>
        <div v-if="selectedEventDesc" class="event-desc">{{ selectedEventDesc }}</div>
      </el-form-item>

      <el-form-item label="是否介入">
        <el-radio-group v-model="form.is_intervened">
          <el-radio :value="true">是</el-radio>
          <el-radio :value="false">否</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="采取行动">
        <el-input v-model="form.action_taken" type="textarea" :rows="2" placeholder="你做了什么/准备做什么" />
      </el-form-item>

      <el-form-item label="理由与依据">
        <el-input v-model="form.reasoning" type="textarea" :rows="3" placeholder="你的判断依据、价值取向、伦理考量..." />
      </el-form-item>

      <el-form-item label="心理状态">
        <el-input v-model="form.psychological_state" type="textarea" :rows="2" placeholder="当时的感受、压力、犹豫点..." />
      </el-form-item>

      <el-form-item label="替代方案">
        <el-input v-model="form.alternatives" type="textarea" :rows="2" placeholder="可能的其他选择..." />
      </el-form-item>

      <el-form-item label="预期结果">
        <el-input v-model="form.expected_outcome" type="textarea" :rows="2" placeholder="希望达到什么效果" />
      </el-form-item>

      <el-form-item label="实际结果">
        <el-input v-model="form.actual_outcome" type="textarea" :rows="2" placeholder="发生了什么（可后补）" />
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
  keyEvents: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:modelValue'])

const form = reactive({
  decision_id: undefined,
  key_event_index: null,
  key_event_desc: '',
  is_intervened: true,
  action_taken: '',
  reasoning: '',
  psychological_state: '',
  alternatives: '',
  expected_outcome: '',
  actual_outcome: ''
})

const selectedEventDesc = computed(() => {
  const idx = form.key_event_index
  if (idx === null || idx === undefined) return ''
  const e = props.keyEvents[idx]
  if (typeof e === 'string') return e
  return e?.desc ?? e?.content ?? JSON.stringify(e)
})

watch(
  () => props.modelValue,
  (v) => {
    const d = v || {}
    form.decision_id = d.decision_id ?? d.decisionId
    form.key_event_index = d.key_event_index ?? d.keyEventIndex ?? null
    form.key_event_desc = d.key_event_desc ?? d.keyEventDesc ?? ''
    form.is_intervened = d.is_intervened ?? d.isIntervened ?? true
    form.action_taken = d.action_taken ?? d.actionTaken ?? ''
    form.reasoning = d.reasoning ?? ''
    form.psychological_state = d.psychological_state ?? d.psychologicalState ?? ''
    form.alternatives = d.alternatives ?? ''
    form.expected_outcome = d.expected_outcome ?? d.expectedOutcome ?? ''
    form.actual_outcome = d.actual_outcome ?? d.actualOutcome ?? ''
  },
  { immediate: true, deep: true }
)

watch(
  () => selectedEventDesc.value,
  (v) => {
    form.key_event_desc = v
    emit('update:modelValue', { ...form })
  }
)

watch(
  form,
  () => {
    emit('update:modelValue', { ...form })
  },
  { deep: true }
)
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
.event-desc {
  margin-top: 8px;
  color: #909399;
  white-space: pre-wrap;
  line-height: 1.5;
}
</style>

