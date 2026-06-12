<template>
  <el-card shadow="never">
    <template #header>
      <div class="header-row">
        <div class="module-title">
          <span class="bar" />
          <span class="text">专业问题识别</span>
        </div>
        <el-button type="primary" size="small" icon="Plus" @click="handleAdd">新增问题</el-button>
      </div>
    </template>
    <div v-if="problems.length === 0" class="empty">暂无结果，点击「新增问题」手动添加</div>
    <div v-else class="problem-grid">
      <div v-for="(p, idx) in problems" :key="idx" class="problem-card">
        <div class="problem-top">
          <div class="problem-badge">问题 {{ idx + 1 }}</div>
          <div class="problem-actions">
            <el-button link type="primary" size="small" @click="handleEdit(idx)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(idx)">删除</el-button>
          </div>
        </div>
        <div class="problem-title">{{ formatProblemTitle(p) }}</div>
        <div v-if="formatProblemDomain(p)" class="problem-domain">
          <span class="domain-badge">{{ formatProblemDomain(p) }}</span>
        </div>
        <div class="problem-desc">{{ formatProblemDesc(p) }}</div>
      </div>
    </div>

    <!-- 新增 / 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑专业问题' : '新增专业问题'"
      width="520px"
      destroy-on-close
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="问题标题">
          <el-input v-model="form.title" placeholder="请输入问题标题" />
        </el-form-item>
        <el-form-item label="社工领域">
          <el-input v-model="form.domain" placeholder="例如：老年社工、危机干预" />
        </el-form-item>
        <el-form-item label="详细描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入问题的详细描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirm">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  problems: {
    type: Array,
    default: () => []
  }
})
const emit = defineEmits(['update:problems'])

const dialogVisible = ref(false)
const isEdit = ref(false)
const editIndex = ref(-1)
const form = reactive({ title: '', domain: '', description: '' })

/* ---------- CRUD handlers ---------- */

function handleAdd() {
  isEdit.value = false
  editIndex.value = -1
  form.title = ''
  form.domain = ''
  form.description = ''
  dialogVisible.value = true
}

function handleEdit(idx) {
  isEdit.value = true
  editIndex.value = idx
  const obj = normalizeMaybeJson(props.problems[idx])
  form.title = typeof obj === 'string' ? obj : (obj?.title ?? obj?.name ?? '')
  form.domain = typeof obj === 'string' ? '' : (obj?.domain ?? '')
  form.description = typeof obj === 'string' ? '' : (obj?.description ?? obj?.desc ?? obj?.content ?? '')
  dialogVisible.value = true
}

function handleDelete(idx) {
  ElMessageBox.confirm('确定删除该专业问题？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const list = [...props.problems]
    list.splice(idx, 1)
    emit('update:problems', list)
    ElMessage.success('已删除')
  }).catch(() => {})
}

function handleConfirm() {
  if (!form.title.trim()) {
    ElMessage.warning('请输入问题标题')
    return
  }
  const item = {
    title: form.title.trim(),
    domain: form.domain.trim(),
    description: form.description.trim()
  }
  const list = [...props.problems]
  if (isEdit.value) {
    list[editIndex.value] = item
  } else {
    list.push(item)
  }
  emit('update:problems', list)
  dialogVisible.value = false
  ElMessage.success(isEdit.value ? '已更新' : '已添加')
}

/* ---------- helpers ---------- */

function formatProblemTitle(p) {
  const obj = normalizeMaybeJson(p)
  if (typeof obj === 'string') return obj
  return obj?.title ?? obj?.name ?? `问题`
}

function formatProblemDomain(p) {
  const obj = normalizeMaybeJson(p)
  if (typeof obj === 'string') return ''
  return obj?.domain ?? ''
}

function formatProblemDesc(p) {
  const obj = normalizeMaybeJson(p)
  if (typeof obj === 'string') return ''
  return obj?.description ?? obj?.desc ?? obj?.content ?? ''
}

function normalizeMaybeJson(v) {
  if (!v) return ''
  if (typeof v !== 'string') return v
  const s = v.trim()
  if (!s) return ''
  if (s.startsWith('{') && s.endsWith('}')) {
    try {
      return JSON.parse(s)
    } catch {
      return s
    }
  }
  return s
}
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.module-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
}
.bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: #3b82f6;
}
.empty {
  color: #909399;
  padding: 16px 0;
  text-align: center;
}
.problem-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
@media (max-width: 768px) {
  .problem-grid {
    grid-template-columns: 1fr;
  }
}
.problem-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 20px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.problem-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}
.problem-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.problem-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 9999px;
  background: #eff6ff;
  color: #3b82f6;
  font-size: 13px;
  font-weight: 600;
}
.problem-actions {
  display: flex;
  gap: 4px;
}
.problem-title {
  margin-top: 8px;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}
.problem-domain {
  margin-bottom: 8px;
}
.domain-badge {
  display: inline-flex;
  padding: 4px 8px;
  border-radius: 6px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 12px;
}
.problem-desc {
  margin-top: 10px;
  font-size: 15px;
  color: #4b5563;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
