<template>
  <div class="assistant-message">
    <div ref="markdownRef" class="assistant-markdown" @click="handleInlineClick">
      <MarkdownRender :content="content" :is-dark="isDark" />
    </div>

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
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";
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
});

const emit = defineEmits(["open-citation"]);

const markdownRef = ref(null);

// 把已渲染 Markdown 里的 [n] 文本节点包成可点击标记（只包纯文本，不注入 HTML）
function wrapCitations() {
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
  () => [props.content, props.streaming],
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
  align-items: center;
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
}
.citation-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.citation-locator {
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.citation-arrow {
  color: var(--el-text-color-placeholder);
}
</style>
