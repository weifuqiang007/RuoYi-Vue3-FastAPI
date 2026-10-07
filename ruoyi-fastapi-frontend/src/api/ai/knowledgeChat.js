import request from "@/utils/request";

// 获取授权知识库列表
export function listKnowledgeBases() {
  return request({
    url: "/ai/knowledge-chat/knowledge-bases",
    method: "get",
  });
}

// 创建知识对话会话
export function createKnowledgeChatSession(data) {
  return request({
    url: "/ai/knowledge-chat/sessions",
    method: "post",
    data: data,
  });
}

// 获取知识对话会话列表
export function listKnowledgeChatSessions(params) {
  return request({
    url: "/ai/knowledge-chat/sessions",
    method: "get",
    params: params,
  });
}

// 获取会话消息历史
export function listKnowledgeChatMessages(sessionId, params) {
  return request({
    url: "/ai/knowledge-chat/sessions/" + sessionId + "/messages",
    method: "get",
    params: params,
  });
}

// 获取引用详情（含原文，二次鉴权）
export function getKnowledgeChatCitation(messageId, citationNo) {
  return request({
    url:
      "/ai/knowledge-chat/messages/" + messageId + "/citations/" + citationNo,
    method: "get",
  });
}

// 停止生成
export function cancelKnowledgeChatMessage(messageId) {
  return request({
    url: "/ai/knowledge-chat/messages/" + messageId + "/cancel",
    method: "post",
  });
}
