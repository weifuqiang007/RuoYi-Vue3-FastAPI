<template>
  <div class="app-container knowledge-chat-page">
    <el-container class="chat-container">
      <!-- 左侧：会话管理 -->
      <el-aside width="248px" class="chat-aside">
        <SessionSidebar
          :sessions="sessions"
          :active-session-id="activeSessionId"
          :loading="sessionsLoading"
          @new-session="handleNewSession"
          @select="handleSelectSession"
        />
      </el-aside>

      <el-container class="chat-main">
        <!-- 顶部：标题 + 资料范围 -->
        <el-header height="64px" class="chat-header">
          <div class="header-title">社会工作教学与研究助手</div>
          <div class="header-scope">
            <span class="scope-label">资料范围</span>
            <el-select
              v-model="selectedKbIds"
              multiple
              collapse-tags
              collapse-tags-tooltip
              :max-collapse-tags="2"
              placeholder="请选择资料范围"
              class="scope-select"
              :disabled="sending"
              @change="handleKbChange"
            >
              <el-option
                v-for="kb in kbOptions"
                :key="kb.kbId"
                :label="kb.kbName"
                :value="String(kb.kbId)"
              />
            </el-select>
          </div>
        </el-header>

        <!-- 中部：消息列表 -->
        <el-main class="chat-body" ref="bodyRef">
          <div v-if="messages.length === 0" class="chat-welcome">
            <div class="welcome-title">从一个教学或研究问题开始</div>
            <div class="welcome-desc">
              结合已选教材与文章回答，支持连续追问和来源核查
            </div>
            <div v-if="selectedKbIds.length === 0" class="welcome-hint">请先选择资料范围</div>
            <div v-if="kbOptions.length === 0" class="welcome-hint">暂无可用资料，请联系管理员配置</div>
            <div v-if="kbOptions.length > 0 && selectedKbIds.length > 0" class="welcome-examples">
              <div
                v-for="(q, i) in exampleQuestions"
                :key="i"
                class="example-item"
                @click="fillExample(q)"
              >
                {{ q }}
              </div>
            </div>
          </div>

          <div v-else class="message-list">
            <div v-for="(msg, index) in messages" :key="index" class="message-row" :class="`role-${msg.role}`">
              <template v-if="msg.role === 'user'">
                <div class="user-bubble">{{ msg.content }}</div>
              </template>
              <template v-else>
                <div class="assistant-wrap">
                  <AssistantMessage
                    v-if="msg.status !== 'failed'"
                    :content="msg.content"
                    :citations="msg.citations"
                    :streaming="msg.streaming"
                    @open-citation="(no) => openCitation(no, msg)"
                  />
                  <el-alert
                    v-else
                    type="error"
                    :closable="false"
                    title="生成失败"
                    :description="msg.errorText || '回答未完成，不作为可靠依据'"
                    show-icon
                  />
                  <div v-if="msg.citationStatus === 'needs_review'" class="citation-warning">
                    部分引用未通过校验，请勿直接作为理论依据
                  </div>
                </div>
              </template>
            </div>

            <div v-if="stage" class="stage-tip">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>{{ stageText }}</span>
            </div>
          </div>
        </el-main>

        <!-- 底部：输入区 -->
        <el-footer height="auto" class="chat-composer">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="2"
            maxlength="4000"
            show-word-limit
            :autosize="{ minRows: 2, maxRows: 6 }"
            placeholder="输入问题，Enter 发送，Shift+Enter 换行"
            :disabled="sending"
            @keydown.enter.exact.prevent="handleSend"
          />
          <div class="composer-actions">
            <span class="composer-note">辅助教学与研究，重要结论请核对原文</span>
            <el-button
              type="primary"
              :loading="sending"
              :disabled="!canSend"
              @click="handleSend"
            >
              发送
            </el-button>
          </div>
        </el-footer>
      </el-container>
    </el-container>

    <SourceDrawer
      v-model="drawerVisible"
      :message-id="drawerMessageId"
      :citation-no="drawerCitationNo"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import { getToken } from "@/utils/auth";
import { Loading } from "@element-plus/icons-vue";
import {
  listKnowledgeBases,
  listKnowledgeChatSessions,
  listKnowledgeChatMessages,
} from "@/api/ai/knowledgeChat";
import SessionSidebar from "./components/SessionSidebar.vue";
import AssistantMessage from "./components/AssistantMessage.vue";
import SourceDrawer from "./components/SourceDrawer.vue";

const exampleQuestions = [
  "赋权理论与优势视角有什么联系和区别？",
  "社会工作者如何反思自己在服务关系中的权力位置？",
  "请根据知识库资料解释反身性与一般反思的区别。",
];

const sessions = ref([]);
const sessionsLoading = ref(false);
const activeSessionId = ref("");
const kbOptions = ref([]);
const selectedKbIds = ref([]);

const messages = ref([]);
const inputMessage = ref("");
const sending = ref(false);
const stage = ref("");
const abortController = ref(null);

const bodyRef = ref(null);

const drawerVisible = ref(false);
const drawerMessageId = ref(null);
const drawerCitationNo = ref(null);

const stageText = computed(() => {
  return stage.value === "retrieving" ? "正在检索资料" : "正在生成回答";
});

const canSend = computed(() => {
  return inputMessage.value.trim().length > 0 && selectedKbIds.value.length > 0 && !sending.value;
});

function generateSessionId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return "s-" + Date.now() + "-" + Math.random().toString(16).slice(2);
}

function generateRequestId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return "r-" + Date.now() + "-" + Math.random().toString(16).slice(2);
}

async function loadKnowledgeBases() {
  try {
    const resp = await listKnowledgeBases();
    kbOptions.value = resp.data || [];
  } catch (e) {
    kbOptions.value = [];
  }
}

async function loadSessions() {
  sessionsLoading.value = true;
  try {
    const resp = await listKnowledgeChatSessions({ pageNum: 1, pageSize: 50 });
    sessions.value = (resp.data && resp.data.items) || [];
  } catch (e) {
    sessions.value = [];
  } finally {
    sessionsLoading.value = false;
  }
}

async function loadMessages(sessionId) {
  try {
    const resp = await listKnowledgeChatMessages(sessionId, { pageNum: 1, pageSize: 200 });
    const items = (resp.data && resp.data.items) || [];
    messages.value = items.map((m) => ({
      role: m.role,
      content: m.content || "",
      messageId: m.messageId,
      status: m.status || "completed",
      answerType: m.answerType,
      citationStatus: m.citationStatus,
      citations: m.citations || [],
      streaming: false,
    }));
    if (messages.value.length > 0) {
      // 历史会话优先展示该会话最后选定的资料范围（后端会话里保存）
      const session = sessions.value.find((s) => s.sessionId === sessionId);
      if (session && session.kbIds && session.kbIds.length) {
        selectedKbIds.value = session.kbIds.map(String);
      }
    }
  } catch (e) {
    messages.value = [];
  }
  scrollToBottom();
}

function handleNewSession() {
  if (sending.value) {
    return;
  }
  activeSessionId.value = generateSessionId();
  messages.value = [];
  inputMessage.value = "";
  stage.value = "";
}

function handleSelectSession(session) {
  if (sending.value) {
    return;
  }
  activeSessionId.value = session.sessionId;
  inputMessage.value = "";
  loadMessages(session.sessionId);
}

function handleKbChange() {
  if (sending.value) {
    return;
  }
}

function fillExample(question) {
  inputMessage.value = question;
}

function scrollToBottom() {
  nextTick(() => {
    if (bodyRef.value) {
      bodyRef.value.$el.scrollTop = bodyRef.value.$el.scrollHeight;
    }
  });
}

function pushUserMessage(content) {
  messages.value.push({ role: "user", content, streaming: false });
}

function pushAssistantPlaceholder() {
  messages.value.push({
    role: "assistant",
    content: "",
    citations: [],
    streaming: true,
    status: "generating",
    messageId: null,
  });
  return messages.value.length - 1;
}

async function handleSend() {
  if (!canSend.value) return;
  const text = inputMessage.value.trim();
  if (text.length > 4000) return;

  sending.value = true;
  inputMessage.value = "";
  stage.value = "retrieving";

  const sessionId = activeSessionId.value || generateSessionId();
  activeSessionId.value = sessionId;

  pushUserMessage(text);
  const assistantIndex = pushAssistantPlaceholder();
  scrollToBottom();

  abortController.value = new AbortController();

  try {
    const response = await fetch(
      import.meta.env.VITE_APP_BASE_API +
        "/ai/knowledge-chat/sessions/" +
        sessionId +
        "/messages/stream",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + getToken(),
        },
        signal: abortController.value.signal,
        body: JSON.stringify({
          content: text,
          kbIds: selectedKbIds.value,
          clientRequestId: generateRequestId(),
        }),
      }
    );

    if (!response.ok) {
      throw new Error("请求失败: HTTP " + response.status);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let assistantMsg = messages.value[assistantIndex];

    while (true) {
      if (!abortController.value) break;
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;
        let data;
        try {
          data = JSON.parse(line);
        } catch (e) {
          continue;
        }
        handleStreamEvent(data, assistantIndex);
      }
    }
  } catch (err) {
    if (err.name === "AbortError") {
      // 用户终止，不额外提示
    } else {
      const assistantMsg = messages.value[assistantIndex];
      if (assistantMsg) {
        assistantMsg.streaming = false;
        assistantMsg.status = "failed";
        assistantMsg.errorText = err.message || "请求失败";
      }
    }
  } finally {
    sending.value = false;
    stage.value = "";
    abortController.value = null;
    loadSessions();
    scrollToBottom();
  }
}

function handleStreamEvent(data, assistantIndex) {
  const assistantMsg = messages.value[assistantIndex];
  if (!assistantMsg) return;

  switch (data.type) {
    case "meta":
      activeSessionId.value = data.sessionId;
      assistantMsg.messageId = data.messageId;
      break;
    case "status":
      stage.value = data.stage;
      break;
    case "delta":
      assistantMsg.content += data.content || "";
      break;
    case "citations":
      assistantMsg.citations = data.items || [];
      break;
    case "done":
      if (data.finalContent) {
        assistantMsg.content = data.finalContent;
      }
      assistantMsg.status = data.status || "completed";
      assistantMsg.answerType = data.answerType;
      assistantMsg.citationStatus = data.citationStatus;
      assistantMsg.streaming = false;
      break;
    case "error":
      assistantMsg.streaming = false;
      assistantMsg.status = "failed";
      assistantMsg.errorText = data.message || "生成失败";
      break;
    case "duplicate":
      activeSessionId.value = data.sessionId;
      // 重复提交：直接刷新历史，不追加
      loadMessages(data.sessionId);
      break;
    default:
      break;
  }
}

function openCitation(citationNo, msg) {
  if (!msg || msg.messageId == null) return;
  drawerMessageId.value = msg.messageId;
  drawerCitationNo.value = citationNo;
  drawerVisible.value = true;
}

onMounted(() => {
  loadKnowledgeBases();
  loadSessions();
});
</script>

<style scoped>
.knowledge-chat-page {
  padding: 0;
}
.chat-container {
  height: calc(100vh - 84px);
}
.chat-aside {
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}
.chat-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}
.header-title {
  font-size: 16px;
  font-weight: 600;
}
.header-scope {
  display: flex;
  align-items: center;
  gap: 8px;
}
.scope-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}
.scope-select {
  width: 300px;
}
.chat-body {
  background: var(--el-fill-color-lighter);
  padding: 16px 24px;
}
.chat-welcome {
  max-width: 960px;
  margin: 80px auto 0;
  text-align: center;
}
.welcome-title {
  font-size: 22px;
  font-weight: 600;
}
.welcome-desc {
  margin-top: 10px;
  color: var(--el-text-color-secondary);
}
.welcome-hint {
  margin-top: 20px;
  color: var(--el-text-color-secondary);
}
.welcome-examples {
  max-width: 560px;
  margin: 28px auto 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.example-item {
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  color: var(--el-text-color-primary);
  transition: border-color 0.15s;
}
.example-item:hover {
  border-color: var(--el-color-primary);
}
.message-list {
  max-width: 960px;
  margin: 0 auto;
}
.message-row {
  margin-bottom: 20px;
}
.role-user {
  display: flex;
  justify-content: flex-end;
}
.user-bubble {
  max-width: 70%;
  background: var(--el-color-primary);
  color: #fff;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
}
.assistant-wrap {
  max-width: 100%;
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 16px 18px;
}
.citation-warning {
  margin-top: 10px;
  font-size: 13px;
  color: var(--el-color-warning);
}
.stage-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}
.chat-composer {
  padding: 12px 24px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}
.composer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
.composer-note {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
