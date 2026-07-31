# RAG 检索接口：增加精排分数与溯源元数据

> 版本：V1.1  
> 日期：2026-07-28  
> 变更类型：出参变更（向后兼容）

## 接口信息

- URL：`POST /rag/retrieval/search`
- 名称：混合检索
- 入参：不变

## 变更内容

原有 `chunk_id`、`doc_id`、`content`、`score` 字段保留，新增：

| 字段 | 类型 | 含义 |
|---|---|---|
| `kb_id` | integer | 分块所属知识库 ID |
| `vector_score` | number | 向量召回原始相似度 |
| `keyword_score` | number | 中英混合 BM25 分数 |
| `fusion_score` | number | RRF 融合分数 |
| `rerank_score` | number | 精排后的最终相关性分数 |
| `metadata` | object | 溯源信息，包含文档名、页码、章节路径和块类型 |

`score` 的含义由“某一路粗召回分数”修正为“最终精排分数”。结果仍按 `score` 降序。

## 前端需要做的事情

1. 排名展示继续使用 `score`，不要拿 `vector_score` 单独排序。
2. 引用卡片优先展示 `metadata.doc_name`、`metadata.page`、`metadata.heading_path`。
3. 调试页可同时展示四阶段分数，便于判断问题发生在召回、融合还是精排。

## 测试示例

```bash
curl -X POST 'http://localhost:9099/dev-api/rag/retrieval/search' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"query":"反身性如何体现权力位置","kb_ids":[1],"top_k":5}'
```

预期：结果按 `score` 降序，且每项包含 `metadata.doc_name`；Markdown 文档应包含非空的 `metadata.heading_path`。
