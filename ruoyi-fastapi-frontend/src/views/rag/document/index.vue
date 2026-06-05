<template>
  <div class="app-container">
    <el-row :gutter="10" class="mb8">
      <el-col :span="6">
        <el-select
          v-model="selectedKbId"
          placeholder="全部知识库"
          clearable
          @change="handleFilterChange"
          style="width: 100%"
        >
          <el-option label="全部知识库" :value="null" />
          <el-option
            v-for="kb in kbOptions"
            :key="kb.kb_id"
            :label="kb.kb_name"
            :value="kb.kb_id"
          />
        </el-select>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="Upload"
          @click="handleUploadClick"
          v-hasPermi="['rag:document:add']"
        >
          上传文档
        </el-button>
      </el-col>
    </el-row>

    <el-table v-loading="loading" :data="docList">
      <el-table-column label="文档名称" prop="doc_name" min-width="200" show-overflow-tooltip />
      <el-table-column label="所属知识库" width="150" align="center">
        <template #default="scope">
          {{ getKbName(scope.row.kb_id) }}
        </template>
      </el-table-column>
      <el-table-column label="类型" prop="file_type" width="80" align="center" />
      <el-table-column label="大小" width="100" align="center">
        <template #default="scope">
          {{ formatFileSize(scope.row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column label="解析状态" width="100" align="center">
        <template #default="scope">
          <el-tag :type="parseStatusType(scope.row.parse_status)">
            {{ parseStatusLabel(scope.row.parse_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="向量化状态" width="100" align="center">
        <template #default="scope">
          <el-tag :type="embedStatusType(scope.row.embed_status)">
            {{ embedStatusLabel(scope.row.embed_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="分块数" prop="chunk_count" width="80" align="center" />
      <el-table-column label="创建时间" prop="create_time" width="170" />
      <el-table-column label="操作" width="120" align="center">
        <template #default="scope">
          <el-button link type="primary" icon="Download" @click="handleDownload(scope.row)">
            下载
          </el-button>
          <el-button
            link
            type="danger"
            icon="Delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['rag:document:remove']"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog title="上传文档" v-model="uploadDialogVisible" width="500px">
      <el-form label-width="100px">
        <el-form-item label="目标知识库" required>
          <el-select v-model="uploadKbId" placeholder="请选择知识库" style="width: 100%">
            <el-option
              v-for="kb in kbOptions"
              :key="kb.kb_id"
              :label="kb.kb_name"
              :value="kb.kb_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="选择文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".pdf,.docx,.doc,.txt,.md"
          >
            <el-button type="primary" plain>选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 PDF、Word、TXT、Markdown 格式</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取 消</el-button>
        <el-button
          type="primary"
          @click="submitUpload"
          :loading="uploading"
          :disabled="!uploadKbId || !uploadFile"
        >
          确 定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listAllDocument, uploadDocument, downloadDocument, delDocument } from '@/api/rag/document'
import { listKnowledgeBase } from '@/api/rag/knowledgeBase'

const loading = ref(false)
const docList = ref([])
const kbOptions = ref([])
const selectedKbId = ref(null)

const uploadDialogVisible = ref(false)
const uploadKbId = ref(null)
const uploadFile = ref(null)
const uploading = ref(false)
const uploadRef = ref()

async function getKbOptions() {
  const res = await listKnowledgeBase()
  kbOptions.value = res.data || []
}

async function getList() {
  loading.value = true
  try {
    const res = await listAllDocument(selectedKbId.value)
    docList.value = res.data || []
  } finally {
    loading.value = false
  }
}

function handleFilterChange() {
  getList()
}

function getKbName(kbId) {
  const kb = kbOptions.value.find(k => k.kb_id === kbId)
  return kb ? kb.kb_name : `ID: ${kbId}`
}

function handleUploadClick() {
  uploadKbId.value = selectedKbId.value || null
  uploadFile.value = null
  uploadDialogVisible.value = true
}

function handleFileChange(file) {
  const allowed = new Set(['.pdf', '.docx', '.doc', '.txt', '.md'])
  const name = file?.name || ''
  const lastDot = name.lastIndexOf('.')
  const ext = lastDot >= 0 ? name.slice(lastDot).toLowerCase() : ''
  if (!allowed.has(ext)) {
    ElMessage.error('仅支持 PDF、Word、TXT、Markdown 格式')
    uploadRef.value?.clearFiles?.()
    uploadFile.value = null
    return
  }
  uploadFile.value = file.raw
}

function handleFileRemove() {
  uploadFile.value = null
}

async function submitUpload() {
  if (!uploadKbId.value) {
    ElMessage.warning('请选择目标知识库')
    return
  }
  if (!uploadFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  uploading.value = true
  try {
    await uploadDocument(uploadKbId.value, uploadFile.value)
    ElMessage.success('上传成功，正在处理中...')
    uploadDialogVisible.value = false
    setTimeout(() => getList(), 2000)
  } finally {
    uploading.value = false
  }
}

async function handleDownload(row) {
  try {
    const data = await downloadDocument(row.doc_id)
    const blob = data instanceof Blob ? data : new Blob([data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = row.doc_name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载失败')
  }
}

function handleDelete(row) {
  ElMessageBox.confirm(`确认删除文档「${row.doc_name}」？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      await delDocument(row.doc_id)
      ElMessage.success('删除成功')
      await getList()
    })
    .catch(() => {})
}

function parseStatusLabel(s) {
  const key = String(s ?? '')
  return { '0': '待处理', '1': '解析中', '2': '完成', '9': '失败' }[key] || '未知'
}

function parseStatusType(s) {
  const key = String(s ?? '')
  return { '0': 'info', '1': 'warning', '2': 'success', '9': 'danger' }[key] || 'info'
}

function embedStatusLabel(s) {
  const key = String(s ?? '')
  return { '0': '待处理', '1': '向量化中', '2': '完成', '9': '失败' }[key] || '未知'
}

function embedStatusType(s) {
  const key = String(s ?? '')
  return { '0': 'info', '1': 'warning', '2': 'success', '9': 'danger' }[key] || 'info'
}

function formatFileSize(bytes) {
  const value = Number(bytes || 0)
  if (!value) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = value
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return size.toFixed(1) + ' ' + units[i]
}

watch(uploadDialogVisible, visible => {
  if (visible) {
    uploadRef.value?.clearFiles?.()
  } else {
    uploadRef.value?.clearFiles?.()
    uploadFile.value = null
  }
})

onMounted(async () => {
  await getKbOptions()
  await getList()
})
</script>

