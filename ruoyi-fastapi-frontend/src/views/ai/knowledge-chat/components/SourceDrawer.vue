<template>
  <el-drawer
    v-model="visible"
    :size="drawerSize"
    :with-header="true"
    :before-close="handleClose"
    direction="rtl"
  >
    <template #header>
      <span class="drawer-title">引用来源</span>
    </template>

    <div v-if="loading" class="drawer-loading">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="unavailable" class="drawer-unavailable">
      <el-empty description="该来源已不可访问" />
    </div>

    <div v-else-if="citation" class="citation-detail">
      <div class="detail-title">{{ citation.title || "未命名文献" }}</div>
      <el-descriptions :column="1" border size="small" class="detail-meta">
        <el-descriptions-item v-if="citation.authors && citation.authors.length" label="作者">
          {{ citation.authors.join("、") }}
        </el-descriptions-item>
        <el-descriptions-item label="文献类型">
          {{ sourceTypeText }}
        </el-descriptions-item>
        <el-descriptions-item v-if="citation.headingPath && citation.headingPath.length" label="章节">
          {{ citation.headingPath.join(" › ") }}
        </el-descriptions-item>
        <el-descriptions-item v-if="citation.pageLabel" label="页码">
          {{ citation.pageLabel }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="detail-excerpt-title">原文片段</div>
      <div class="detail-excerpt">{{ citation.excerpt || "未记录原文片段" }}</div>
    </div>
  </el-drawer>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { getKnowledgeChatCitation } from "@/api/ai/knowledgeChat";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  messageId: {
    type: [Number, String],
    default: null,
  },
  citationNo: {
    type: Number,
    default: null,
  },
});

const emit = defineEmits(["update:modelValue"]);

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const drawerSize = computed(() => {
  if (typeof window === "undefined") return "440px";
  return window.innerWidth < 768 ? "100%" : "440px";
});

const loading = ref(false);
const citation = ref(null);
const unavailable = ref(false);

const sourceTypeText = computed(() => {
  const map = { textbook: "教材", article: "文章", other: "其他" };
  return map[citation.value?.sourceType] || citation.value?.sourceType || "其他";
});

watch(
  () => [props.modelValue, props.messageId, props.citationNo],
  async ([open, messageId, citationNo]) => {
    if (!open || messageId == null || citationNo == null) return;
    loading.value = true;
    citation.value = null;
    unavailable.value = false;
    try {
      const resp = await getKnowledgeChatCitation(messageId, citationNo);
      if (resp.code === 200 && resp.data) {
        if (resp.data.availability === "unavailable") {
          unavailable.value = true;
        } else {
          citation.value = resp.data;
        }
      } else {
        unavailable.value = true;
      }
    } catch (e) {
      unavailable.value = true;
    } finally {
      loading.value = false;
    }
  }
);

function handleClose() {
  emit("update:modelValue", false);
}
</script>

<style scoped>
.drawer-title {
  font-weight: 600;
}
.drawer-loading {
  padding: 16px;
}
.drawer-unavailable {
  padding-top: 40px;
}
.citation-detail {
  padding: 4px 4px 24px;
}
.detail-title {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 14px;
  line-height: 1.5;
}
.detail-meta {
  margin-bottom: 18px;
}
.detail-excerpt-title {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}
.detail-excerpt {
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  padding: 12px 14px;
  max-height: 60vh;
  overflow-y: auto;
}
</style>
