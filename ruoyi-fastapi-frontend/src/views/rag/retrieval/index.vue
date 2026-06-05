<template>
  <div class="app-container">
    <el-row :gutter="20">
      <el-col :span="10">
        <el-card shadow="never">
          <template #header>检索测试</template>

          <el-form label-width="100px">
            <el-form-item label="知识库">
              <el-select v-model="queryParams.kb_ids" multiple placeholder="选择知识库" style="width: 100%">
                <el-option
                  v-for="kb in kbOptions"
                  :key="kb.kb_id"
                  :label="kb.kb_name"
                  :value="kb.kb_id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="查询文本">
              <el-input v-model="queryParams.query" type="textarea" :rows="4" placeholder="输入要检索的问题..." />
            </el-form-item>
            <el-form-item label="返回数量">
              <el-input-number v-model="queryParams.top_k" :min="1" :max="20" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch" :loading="searching">检索</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card shadow="never">
          <template #header>检索结果（{{ results.length }} 条）</template>

          <div v-if="results.length === 0" style="color: #909399; text-align: center; padding: 40px">
            请输入查询文本并点击检索
          </div>

          <div v-for="(item, idx) in results" :key="item.chunk_id ?? idx" class="result-item">
            <div class="result-header">
              <el-tag size="small" type="primary">排名 {{ idx + 1 }}</el-tag>
              <el-tag size="small" type="success">相似度: {{ formatScore(item.score) }}</el-tag>
              <span class="result-doc">文档ID: {{ item.doc_id }}</span>
            </div>
            <div class="result-content">{{ item.content }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listKnowledgeBase } from '@/api/rag/knowledgeBase'
import { searchRetrieval } from '@/api/rag/retrieval'

const kbOptions = ref([])
const searching = ref(false)
const results = ref([])

const queryParams = reactive({
  kb_ids: [],
  query: '',
  top_k: 5
})

async function getKbOptions() {
  const res = await listKnowledgeBase()
  kbOptions.value = res.data || []
}

async function handleSearch() {
  if (queryParams.kb_ids.length === 0) {
    ElMessage.warning('请选择至少一个知识库')
    return
  }
  if (!queryParams.query.trim()) {
    ElMessage.warning('请输入查询文本')
    return
  }
  searching.value = true
  try {
    const res = await searchRetrieval({
      kb_ids: queryParams.kb_ids,
      query: queryParams.query,
      top_k: queryParams.top_k
    })
    results.value = res.data || []
  } finally {
    searching.value = false
  }
}

function formatScore(score) {
  const value = Number(score)
  if (Number.isFinite(value)) {
    return (value * 100).toFixed(1) + '%'
  }
  return '-'
}

onMounted(() => {
  getKbOptions()
})
</script>

<style scoped>
.result-item {
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.result-doc {
  color: #909399;
  font-size: 12px;
}
.result-content {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
}
</style>

