<template>
  <div class="assistant-message">
    <div ref="markdownRef" class="assistant-markdown" @click="handleInlineClick">
      <MarkdownRender :content="content" :is-dark="isDark" />
    </div>

    <!-- 专业研讨：正文行内 [n] 可点击 + 参考来源卡片 -->
    <template v-if="answerMode !== 'public'">
      <div v-if="citations && citations.length" class="citation-cards">
        <div class="citation-cards-title">参考来源</div>
        <div
          v-for="c in citations"
          :key="c.citationNo"
          class="citation-card"
          :class="{ 'is-unavailable': c.availability === 'unavailable' }"
          @click="handleCardClick(c)"
        >
          <span class="citation-no">[{{ c.citationNo }}]</span>
          <span class="citation-title">{{ c.title || "未命名文献" }}</span>
          <span v-if="c.pageLabel" class="citation-locator">{{ c.pageLabel }}</span>
          <span v-else-if="c.headingPath && c.headingPath.length" class="citation-locator">
            {{ c.headingPath.join(" › ") }}
          </span>
          <el-icon class="citation-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </template>

    <!-- 日常求助：正文无编号，底部折叠参考依据，区分直接依据/背景参考 -->
    <template v-else>
      <div v-if="hasCitations" class="public-references">
        <el-collapse v-model="openPanels" class="reference-collapse">
          <el-collapse-item name="refs">
            <template #title>
              <span class="collapse-title">参考依据（{{ citations.length }}）</span>
            </template>

            <div v-if="directCitations.length" class="ref-group">
              <div class="ref-group-title">直接依据</div>
              <div
                v-for="c in directCitations"
                :key="c.citationNo"
                class="citation-card"
                :class="{ 'is-unavailable': c.availability === 'unavailable' }"
                @click="handleCardClick(c)"
              >
                <span class="citation-no">[{{ c.citationNo }}]</span>
                <div class="citation-body">
                  <div class="citation-title">{{ c.title || "上传文档：未命名" }}</div>
                  <div class="citation-locator-line">
                    <span v-if="c.pageLabel">{{ c.pageLabel }}</span>
                    <span v-else-if="c.headingPath && c.headingPath.length">{{ c.headingPath.join(" › ") }}</span>
                  </div>
                  <div v-if="c.supports && c.supports.length" class="citation-supports">
                    <div v-for="(s, i) in c.supports" :key="i" class="support-item">
                      支持：{{ s.statement }}
                    </div>
                  </div>
                  <div v-if="c.applicationNote" class="citation-note">{{ c.applicationNote }}</div>
                </div>
              </div>
            </div>

            <div v-if="backgroundCitations.length" class="ref-group">
              <div class="ref-group-title">背景参考</div>
              <div
                v-for="c in backgroundCitations"
                :key="c.citationNo"
                class="citation-card"
                :class="{ 'is-unavailable': c.availability === 'unavailable' }"
                @click="handleCardClick(c)"
              >
                <span class="citation-no">[{{ c.citationNo }}]</span>
                <div class="citation-body">
                  <div class="citation-title">{{ c.title || "上传文档：未命名" }}</div>
                  <div class="citation-locator-line">
                    <span v-if="c.pageLabel">{{ c.pageLabel }}</span>
                    <span v-else-if="c.headingPath && c.headingPath.length">{{ c.headingPath.join(" › ") }}</span>
                  </div>
                  <div v-if="c.supports && c.supports.length" class="citation-supports">
                    <div v-for="(s, i) in c.supports" :key="i" class="support-item">
                      支持：{{ s.statement }}
                    </div>
                  </div>
                  <div v-if="c.applicationNote" class="citation-note">{{ c.applicationNote }}</div>
                </div>
              </div>
            </div>

            <div v-if="!directCitations.length && backgroundCitations.length" class="background-only-hint">
              以下为一般性建议，参考资料仅提供背景，非具体方法的直接依据
            </div>
          </el-collapse-item>
        </el-collapse>

        <div v-if="retrievalNoMatch" class="no-match-hint">
          本次为一般性建议，未找到直接支持的文献依据
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { ArrowRight } from "@element-plus/icons-vue";
import { MarkdownRender } from "markstream-vue";
import { useDark } from "@vueuse/core";
import "markstream-vue/index.css";

const isDark = useDark();

const props = defineProps({
  content: {
    type: String,
    default: "",
  },
  citations: {
    type: Array,
    default: () => [],
  },
  streaming: {
    type: Boolean,
    default: false,
  },
  answerMode: {
    type: String,
    default: "professional",
  },
  citationStatus: {
    type: String,
    default: "",
  },
  retrievalStatus: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["open-citation"]);

const markdownRef = ref(null);
const openPanels = ref([]);

const hasCitations = computed(() => props.citations && props.citations.length > 0);
const directCitations = computed(() =>
  (props.citations || []).filter((c) => c.evidenceType === "direct")
);
const backgroundCitations = computed(() =>
  (props.citations || []).filter((c) => c.evidenceType !== "direct")
);
const retrievalNoMatch = computed(() => props.retrievalStatus === "no_match");

// 把已渲染 Markdown 里的 [n] 文本节点包成可点击标记（仅专业模式需要，不注入 HTML）
function wrapCitations() {
  if (props.answerMode === "public") return;
  const el = markdownRef.value;
  if (!el) return;
  const textNodes = [];
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) textNodes.push(node);

  const pattern = /\[(\d+)\]/g;
  textNodes.forEach((textNode) => {
    const text = textNode.nodeValue || "";
    if (!pattern.test(text)) {
      pattern.lastIndex = 0;
      return;
    }
    pattern.lastIndex = 0;
    const parent = textNode.parentNode;
    const frag = document.createDocumentFragment();
    let lastIndex = 0;
    let match;
    while ((match = pattern.exec(text)) !== null) {
      if (match.index > lastIndex) {
        frag.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
      }
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "citation-inline";
      btn.textContent = match[0];
      btn.dataset.citationNo = match[1];
      frag.appendChild(btn);
      lastIndex = pattern.lastIndex;
    }
    if (lastIndex < text.length) {
      frag.appendChild(document.createTextNode(text.slice(lastIndex)));
    }
    parent.replaceChild(frag, textNode);
  });
}

watch(
  () => [props.content, props.streaming, props.answerMode],
  async ([, streaming]) => {
    if (streaming) return;
    await nextTick();
    requestAnimationFrame(wrapCitations);
  }
);

function handleInlineClick(event) {
  const target = event.target.closest(".citation-inline");
  if (target && target.dataset.citationNo) {
    emit("open-citation", Number(target.dataset.citationNo));
  }
}

function handleCardClick(citation) {
  if (citation.availability !== "unavailable") {
    emit("open-citation", citation.citationNo);
  }
}
</script>

<style scoped>
.assistant-markdown {
  font-size: 16px;
  line-height: 1.7;
  word-break: break-word;
}
.assistant-markdown :deep(.citation-inline) {
  border: none;
  background: transparent;
  color: var(--el-color-primary);
  cursor: pointer;
  padding: 0 1px;
  font-size: 13px;
  vertical-align: super;
}
.assistant-markdown :deep(.citation-inline:hover) {
  text-decoration: underline;
}
.citation-cards {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.citation-cards-title {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}
.citation-card {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  margin-bottom: 6px;
  border-radius: 6px;
  background: var(--el-fill-color-light);
  cursor: pointer;
  font-size: 13px;
  transition: background 0.15s;
}
.citation-card:hover {
  background: var(--el-fill-color);
}
.citation-card.is-unavailable {
  cursor: not-allowed;
  opacity: 0.6;
}
.citation-no {
  color: var(--el-color-primary);
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}
.citation-body {
  flex: 1;
  min-width: 0;
}
.citation-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}
.citation-locator {
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.citation-locator-line {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 2px;
}
.citation-supports {
  margin-top: 4px;
}
.support-item {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-top: 2px;
}
.citation-note {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  font-style: italic;
}
.citation-arrow {
  color: var(--el-text-color-placeholder);
}

/* 日常模式折叠参考依据 */
.public-references {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.reference-collapse {
  border: none;
}
.collapse-title {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.ref-group {
  margin-bottom: 10px;
}
.ref-group-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 6px;
}
.background-only-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}
.no-match-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}
</style>
