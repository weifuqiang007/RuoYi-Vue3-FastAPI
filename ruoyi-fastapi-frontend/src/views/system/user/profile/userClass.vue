<template>
   <div class="user-class">
      <el-alert
         v-if="isStudent || isTeacher"
         type="info"
         :closable="false"
         title="说明：学生只能归属一个班级；教师可归属多个班级。"
         class="mb12"
      />

      <!-- 学生：单选班级 -->
      <el-form v-if="isStudent" label-width="100px">
         <el-form-item label="所属班级">
            <el-tree-select
               v-model="studentClassId"
               :data="deptOptions"
               :props="{ value: 'id', label: 'label', children: 'children' }"
               value-key="id"
               placeholder="请选择班级"
               clearable
               check-strictly
               style="width: 100%"
            />
         </el-form-item>
         <el-form-item>
            <el-button type="primary" :loading="saving" @click="saveStudent">保 存</el-button>
         </el-form-item>
      </el-form>

      <!-- 教师：多选班级 -->
      <el-form v-else-if="isTeacher" label-width="100px">
         <el-form-item label="所属班级">
            <el-tree-select
               v-model="teacherClassIds"
               :data="deptOptions"
               :props="{ value: 'id', label: 'label', children: 'children' }"
               value-key="id"
               multiple
               collapse-tags
               collapse-tags-tooltip
               placeholder="请选择班级（可多选）"
               clearable
               check-strictly
               style="width: 100%"
            />
         </el-form-item>
         <el-form-item>
            <el-button type="primary" :loading="saving" @click="saveTeacher">保 存</el-button>
         </el-form-item>
      </el-form>

      <!-- 其他角色 -->
      <el-empty v-else description="当前账号无需设置班级" />
   </div>
</template>

<script setup>
import useUserStore from '@/store/modules/user'
import {
   getProfileDeptTree,
   updateMyStudentClass,
   getMyTeacherClasses,
   addMyTeacherClass,
   removeMyTeacherClass
} from '@/api/edu/profile'

const props = defineProps({
   user: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['refresh'])
const { proxy } = getCurrentInstance()

const userStore = useUserStore()
const roles = computed(() => userStore.roles || [])
const isStudent = computed(() => roles.value.includes('student'))
const isTeacher = computed(() => roles.value.includes('teacher'))

const deptOptions = ref([])
const saving = ref(false)

// 学生当前班级（单值）
const studentClassId = ref(null)
// 教师已选班级（多值，classId 数组）
const teacherClassIds = ref([])
// classId -> 关联记录 id 的映射，删除时需要用关联 id
const classIdToTcId = ref({})

async function loadDeptTree() {
   const res = await getProfileDeptTree()
   deptOptions.value = res.data || []
}

async function loadTeacherClasses() {
   const res = await getMyTeacherClasses()
   const list = res.data || []
   teacherClassIds.value = list.map(item => item.class_id ?? item.classId)
   const mapping = {}
   list.forEach(item => {
      const cid = item.class_id ?? item.classId
      mapping[cid] = item.id
   })
   classIdToTcId.value = mapping
}

// 学生当前班级：监听父组件异步加载的 user，取 deptId（与学生 profile.class_id 同步）
watch(
   () => props.user,
   user => {
      if (isStudent.value && user) {
         studentClassId.value = user.deptId ?? null
      }
   },
   { immediate: true }
)

function saveStudent() {
   if (!studentClassId.value) {
      proxy.$modal.msgWarning('请选择班级')
      return
   }
   saving.value = true
   updateMyStudentClass(studentClassId.value)
      .then(() => {
         proxy.$modal.msgSuccess('班级更新成功')
         emit('refresh')
      })
      .finally(() => {
         saving.value = false
      })
}

async function saveTeacher() {
   const nextSet = new Set((teacherClassIds.value || []).map(String))
   const prevSet = new Set(Object.keys(classIdToTcId.value))
   const toAdd = [...nextSet].filter(cid => !prevSet.has(cid))
   const toRemove = [...prevSet].filter(cid => !nextSet.has(cid))

   saving.value = true
   try {
      await Promise.all([
         ...toAdd.map(cid => addMyTeacherClass(Number(cid))),
         ...toRemove.map(cid => removeMyTeacherClass(classIdToTcId.value[cid]))
      ])
      proxy.$modal.msgSuccess('班级更新成功')
      await loadTeacherClasses()
      emit('refresh')
   } finally {
      saving.value = false
   }
}

onMounted(async () => {
   await loadDeptTree()
   if (isTeacher.value) {
      await loadTeacherClasses()
   }
})
</script>

<style scoped>
.mb12 {
   margin-bottom: 12px;
}
</style>
