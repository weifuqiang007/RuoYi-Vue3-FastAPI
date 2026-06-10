<template>
  <AiChatPanel
    title="AI 追问"
    :request-url="requestUrl"
    :build-payload="buildPayload"
  />
</template>

<script setup>
import AiChatPanel from '@/views/learning/components/AiChatPanel.vue'

const props = defineProps({
  scenarioId: {
    type: [String, Number],
    default: null
  }
})

const requestUrl = '/learning/scenario/followup'

function buildPayload(text) {
  return {
    scenario_id: props.scenarioId,
    user_message: text
  }
}
</script>

