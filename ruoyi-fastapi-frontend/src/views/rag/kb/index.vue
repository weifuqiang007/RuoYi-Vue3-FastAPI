<template>
  <div class="app-container">
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="Plus"
          @click="handleAdd"
          v-hasPermi="['rag:kb:add']"
        >
          新增
        </el-button>
      </el-col>
    </el-row>

    <el-table v-loading="loading" :data="kbList">
      <el-table-column label="知识库名称" prop="kb_name" min-width="150" />
      <el-table-column label="描述" prop="kb_desc" min-width="200" show-overflow-tooltip />
      <el-table-column label="文档数" prop="doc_count" width="80" align="center" />
      <el-table-column label="分块大小" prop="chunk_size" width="100" align="center" />
      <el-table-column label="重叠" prop="chunk_overlap" width="80" align="center" />
      <el-table-column label="创建时间" prop="create_time" width="170" />
      <el-table-column label="操作" width="150" align="center">
        <template #default="scope">
          <el-button
            link
            type="primary"
            icon="Edit"
            @click="handleEdit(scope.row)"
            v-hasPermi="['rag:kb:edit']"
          >
            修改
          </el-button>
          <el-button
            link
            type="danger"
            icon="Delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['rag:kb:remove']"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog :title="dialogTitle" v-model="dialogVisible" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="知识库名称" prop="kb_name">
          <el-input v-model="form.kb_name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="kb_desc">
          <el-input v-model="form.kb_desc" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="分块大小" prop="chunk_size">
          <el-input-number v-model="form.chunk_size" :min="100" :max="2000" :step="100" />
        </el-form-item>
        <el-form-item label="分块重叠" prop="chunk_overlap">
          <el-input-number v-model="form.chunk_overlap" :min="0" :max="500" :step="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitForm" :loading="saving">确 定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listKnowledgeBase, addKnowledgeBase, updateKnowledgeBase, delKnowledgeBase } from '@/api/rag/knowledgeBase'

const loading = ref(false)
const saving = ref(false)
const kbList = ref([])
const dialogVisible = ref(false)
const formRef = ref()

const form = reactive({
  kb_id: undefined,
  kb_name: '',
  kb_desc: '',
  chunk_size: 500,
  chunk_overlap: 50
})

const rules = {
  kb_name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }]
}

const dialogTitle = computed(() => (form.kb_id ? '修改知识库' : '新增知识库'))

async function getList() {
  loading.value = true
  try {
    const res = await listKnowledgeBase()
    kbList.value = res.data || []
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.kb_id = undefined
  form.kb_name = ''
  form.kb_desc = ''
  form.chunk_size = 500
  form.chunk_overlap = 50
  formRef.value?.clearValidate?.()
}

function handleAdd() {
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  resetForm()
  Object.assign(form, row)
  dialogVisible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (form.kb_id) {
      await updateKnowledgeBase(form)
      ElMessage.success('修改成功')
    } else {
      await addKnowledgeBase(form)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    await getList()
  } finally {
    saving.value = false
  }
}

function handleDelete(row) {
  ElMessageBox.confirm(`确认删除知识库「${row.kb_name}」？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      await delKnowledgeBase(row.kb_id)
      ElMessage.success('删除成功')
      await getList()
    })
    .catch(() => {})
}

onMounted(() => {
  getList()
})
</script>

