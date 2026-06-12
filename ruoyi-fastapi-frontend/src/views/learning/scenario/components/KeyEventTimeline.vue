<template>
  <el-card shadow="never">
    <template #header>
      <div class="header-row">
        <div class="module-title">
          <span class="bar" />
          <span class="text">关键事件</span>
        </div>
        <el-button type="primary" size="small" icon="Plus" @click="handleAdd">新增事件</el-button>
      </div>
    </template>
    <div v-if="events.length === 0" class="empty">暂无结果，点击「新增事件」手动添加</div>
    <el-timeline v-else class="timeline">
      <el-timeline-item
        v-for="(e, idx) in events"
        :key="idx"
        class="timeline-item"
      >
        <template #dot>
          <div class="dot">{{ idx + 1 }}</div>
        </template>
        <div class="event-card">
          <div class="event-top">
            <div class="event-label">事件 {{ idx + 1 }}</div>
            <div class="event-actions">
              <el-button link type="primary" size="small" @click="handleEdit(idx)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDelete(idx)">删除</el-button>
            </div>
          </div>
          <div class="event-body">{{ formatEvent(e) }}</div>
        </div>
      </el-timeline-item>
    </el-timeline>

    <!-- 新增 / 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑关键事件' : '新增关键事件'"
      width="500px"
      destroy-on-close
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="事件描述">
          <el-input
            v-model="form.event"
            type="textarea"
            :rows="4"
            placeholder="请输入关键事件描述"
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
  events: {
    type: Array,
    default: () => []
  }
})
const emit = defineEmits(['update:events'])

const dialogVisible = ref(false)
const isEdit = ref(false)
const editIndex = ref(-1)
const form = reactive({ event: '' })

/* ---------- CRUD handlers ---------- */

function handleAdd() {
  isEdit.value = false
  editIndex.value = -1
  form.event = ''
  dialogVisible.value = true
}

function handleEdit(idx) {
  isEdit.value = true
  editIndex.value = idx
  const obj = normalizeMaybeJson(props.events[idx])
  form.event = typeof obj === 'string' ? obj : (obj?.event ?? obj?.desc ?? obj?.content ?? obj?.text ?? '')
  dialogVisible.value = true
}

function handleDelete(idx) {
  ElMessageBox.confirm('确定删除该关键事件？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const list = [...props.events]
    list.splice(idx, 1)
    emit('update:events', reindex(list))
    ElMessage.success('已删除')
  }).catch(() => {})
}

function handleConfirm() {
  if (!form.event.trim()) {
    ElMessage.warning('请输入事件描述')
    return
  }
  const list = [...props.events]
  if (isEdit.value) {
    list[editIndex.value] = { index: editIndex.value + 1, event: form.event.trim() }
  } else {
    list.push({ index: list.length + 1, event: form.event.trim() })
  }
  emit('update:events', reindex(list))
  dialogVisible.value = false
  ElMessage.success(isEdit.value ? '已更新' : '已添加')
}

/* ---------- helpers ---------- */

function reindex(list) {
  return list.map((item, i) => ({ ...normalizeMaybeJson(item), index: i + 1 }))
}

function formatEvent(e) {
  const obj = normalizeMaybeJson(e)
  if (typeof obj === 'string') return obj
  return (
    obj?.event ??
    obj?.desc ??
    obj?.content ??
    obj?.text ??
    (obj ? JSON.stringify(obj) : '')
  )
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
.timeline :deep(.el-timeline-item__tail) {
  border-left-color: rgba(59, 130, 246, 0.35);
}
.timeline-item {
  padding-bottom: 18px;
}
.dot {
  width: 22px;
  height: 22px;
  border-radius: 9999px;
  background: #3b82f6;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}
.event-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  padding: 16px;
}
.event-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.event-label {
  font-size: 14px;
  color: #6b7280;
}
.event-actions {
  display: flex;
  gap: 4px;
}
.event-body {
  font-size: 15px;
  color: #1f2937;
  line-height: 1.6;
  white-space: pre-wrap;
}
.empty {
  color: #909399;
  padding: 16px 0;
  text-align: center;
}
</style>
