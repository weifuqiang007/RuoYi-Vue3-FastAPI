<template>
  <div class="app-container">
    <!-- 搜索表单 -->
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="88px">
      <el-form-item label="昵称" prop="nickName">
        <el-input
          v-model="queryParams.nickName"
          placeholder="请输入昵称"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="班级" prop="classId">
        <el-select
          v-model="queryParams.classId"
          placeholder="请选择班级"
          clearable
          style="width: 200px"
        >
          <el-option
            v-for="d in deptOptions"
            :key="d.deptId"
            :label="d.deptName"
            :value="d.deptId"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="学号" prop="studentNo">
        <el-input
          v-model="queryParams.studentNo"
          placeholder="请输入学号"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="审核状态" prop="auditStatus">
        <el-select
          v-model="queryParams.auditStatus"
          placeholder="请选择审核状态"
          clearable
          style="width: 200px"
        >
          <el-option label="待审核" value="0" />
          <el-option label="已通过" value="1" />
          <el-option label="已拒绝" value="2" />
        </el-select>
      </el-form-item>
      <el-form-item label="角色类型" prop="applyRole">
        <el-select
          v-model="queryParams.applyRole"
          placeholder="请选择角色"
          clearable
          style="width: 200px"
        >
          <el-option label="学生" value="student" />
          <el-option label="教师" value="teacher" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="Plus"
          @click="handleAdd"
          v-hasPermi="['edu:audit:add']"
        >新增</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <!-- 表格 -->
    <el-table v-loading="loading" :data="userList">
      <el-table-column label="账号" align="center" prop="userName" min-width="120" />
      <el-table-column label="昵称" align="center" prop="nickName" min-width="100" />
      <el-table-column label="邮箱" align="center" prop="email" min-width="160" />
      <el-table-column label="角色" align="center" min-width="120">
        <template #default="scope">
          <template v-if="scope.row.applyRole === 'student'">
            <div>学号：{{ scope.row.studentNo || '-' }}</div>
            <div>专业：{{ scope.row.major || '-' }}</div>
            <div>年级：{{ scope.row.grade || '-' }}</div>
          </template>
          <template v-else-if="scope.row.applyRole === 'teacher'">
            <div>教师编号：{{ scope.row.teacherNo || '-' }}</div>
            <div>职称：{{ scope.row.title || '-' }}</div>
            <div>研究方向：{{ scope.row.researchArea || '-' }}</div>
          </template>
          <template v-else>-</template>
        </template>
      </el-table-column>
      <el-table-column label="学号/教师编号" align="center" min-width="130">
        <template #default="scope">
          {{ scope.row.applyRole === 'teacher' ? (scope.row.teacherNo || '-') : (scope.row.studentNo || '-') }}
        </template>
      </el-table-column>
      <el-table-column label="班级" align="center" prop="deptName" min-width="120" />
      <el-table-column label="专业" align="center" prop="major" min-width="120" />
      <el-table-column label="年级" align="center" prop="grade" min-width="80" />
      <el-table-column label="注册时间" align="center" prop="createTime" min-width="160" />
      <el-table-column label="审核状态" align="center" min-width="100">
        <template #default="scope">
          <el-tooltip
            v-if="scope.row.auditStatus === '2' && scope.row.auditRemark"
            :content="scope.row.auditRemark"
            placement="top"
          >
            <el-tag type="danger" size="small">已拒绝</el-tag>
          </el-tooltip>
          <el-tag v-else-if="scope.row.auditStatus === '0'" type="warning" size="small">待审核</el-tag>
          <el-tag v-else-if="scope.row.auditStatus === '1'" type="success" size="small">已通过</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" min-width="200" fixed="right">
        <template #default="scope">
          <el-button
            text
            type="primary"
            icon="Edit"
            @click="handleUpdate(scope.row)"
            v-hasPermi="['edu:audit:edit']"
          >编辑</el-button>
          <el-button
            text
            type="danger"
            icon="Delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['edu:audit:remove']"
          >删除</el-button>
          <el-button
            v-if="scope.row.auditStatus === '0'"
            text
            type="warning"
            icon="Check"
            @click="handleAudit(scope.row)"
            v-hasPermi="['edu:audit:audit']"
          >审核</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 新增对话框 -->
    <el-dialog :title="'新增用户'" v-model="addDialogVisible" width="520px" append-to-body>
      <el-tabs v-model="addActiveTab" @tab-change="handleAddTabChange">
        <el-tab-pane label="新增学生" name="student" />
        <el-tab-pane label="新增教师" name="teacher" />
      </el-tabs>
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="100px">
        <template v-if="addActiveTab === 'student'">
          <el-form-item label="学号" prop="studentNo">
            <el-input v-model="addForm.studentNo" placeholder="请输入学号（登录账号）" maxlength="30" />
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="教师编号" prop="teacherNo">
            <el-input v-model="addForm.teacherNo" placeholder="请输入教师编号（登录账号）" maxlength="30" />
          </el-form-item>
        </template>
        <el-form-item label="姓名" prop="nickName">
          <el-input v-model="addForm.nickName" placeholder="请输入姓名" maxlength="30" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="addForm.email" placeholder="请输入邮箱" maxlength="50" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="addForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="addForm.confirmPassword" type="password" placeholder="请再次输入密码" />
        </el-form-item>
        <template v-if="addActiveTab === 'student'">
          <el-form-item label="专业" prop="major">
            <el-input v-model="addForm.major" placeholder="专业（选填）" maxlength="100" />
          </el-form-item>
          <el-form-item label="年级" prop="grade">
            <el-input v-model="addForm.grade" placeholder="年级（选填）" maxlength="20" />
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="职称" prop="title">
            <el-input v-model="addForm.title" placeholder="职称（选填）" maxlength="50" />
          </el-form-item>
          <el-form-item label="研究方向" prop="researchArea">
            <el-input v-model="addForm.researchArea" placeholder="研究方向（选填）" maxlength="200" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="addDialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="submitAdd" :loading="submitLoading">确 定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog :title="'编辑用户'" v-model="editDialogVisible" width="520px" append-to-body>
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="学号" prop="studentNo" v-if="editForm.applyRole === 'student'">
          <el-input v-model="editForm.studentNo" disabled />
        </el-form-item>
        <el-form-item label="教师编号" prop="teacherNo" v-if="editForm.applyRole === 'teacher'">
          <el-input v-model="editForm.teacherNo" disabled />
        </el-form-item>
        <el-form-item label="班级" prop="deptName" v-if="editForm.applyRole === 'student'">
          <el-input v-model="editForm.deptName" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="nickName">
          <el-input v-model="editForm.nickName" placeholder="请输入姓名" maxlength="30" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="请输入邮箱" maxlength="50" />
        </el-form-item>
        <el-form-item label="手机号" prop="phonenumber">
          <el-input v-model="editForm.phonenumber" placeholder="请输入手机号" maxlength="11" />
        </el-form-item>
        <el-form-item label="性别" prop="sex">
          <el-select v-model="editForm.sex" placeholder="请选择性别" style="width: 100%">
            <el-option label="男" value="0" />
            <el-option label="女" value="1" />
            <el-option label="未知" value="2" />
          </el-select>
        </el-form-item>
        <template v-if="editForm.applyRole === 'student'">
          <el-form-item label="专业" prop="major">
            <el-input v-model="editForm.major" placeholder="专业" maxlength="100" />
          </el-form-item>
          <el-form-item label="年级" prop="grade">
            <el-input v-model="editForm.grade" placeholder="年级" maxlength="20" />
          </el-form-item>
        </template>
        <template v-if="editForm.applyRole === 'teacher'">
          <el-form-item label="职称" prop="title">
            <el-input v-model="editForm.title" placeholder="职称" maxlength="50" />
          </el-form-item>
          <el-form-item label="研究方向" prop="researchArea">
            <el-input v-model="editForm.researchArea" placeholder="研究方向" maxlength="200" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editDialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="submitEdit" :loading="submitLoading">确 定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 审核对话框 -->
    <el-dialog :title="'审核用户'" v-model="auditDialogVisible" width="520px" append-to-body>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="账号">{{ auditRow.userName }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ auditRow.nickName }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ auditRow.email }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          {{ auditRow.applyRole === 'student' ? '学生' : '教师' }}
        </el-descriptions-item>
        <template v-if="auditRow.applyRole === 'student'">
          <el-descriptions-item label="学号">{{ auditRow.studentNo }}</el-descriptions-item>
          <el-descriptions-item label="班级">{{ auditRow.deptName }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ auditRow.major }}</el-descriptions-item>
          <el-descriptions-item label="年级">{{ auditRow.grade }}</el-descriptions-item>
        </template>
        <template v-else>
          <el-descriptions-item label="教师编号">{{ auditRow.teacherNo }}</el-descriptions-item>
          <el-descriptions-item label="职称">{{ auditRow.title }}</el-descriptions-item>
          <el-descriptions-item label="研究方向" :span="2">{{ auditRow.researchArea }}</el-descriptions-item>
        </template>
        <el-descriptions-item label="注册时间">{{ auditRow.createTime }}</el-descriptions-item>
      </el-descriptions>
      <el-form ref="auditFormRef" :model="auditForm" :rules="auditRules" label-width="80px" style="margin-top: 16px">
        <el-form-item label="审核备注" prop="auditRemark">
          <el-input
            v-model="auditForm.auditRemark"
            type="textarea"
            placeholder="审核备注（拒绝时建议填写原因）"
            :rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="auditDialogVisible = false">取 消</el-button>
          <el-button type="danger" @click="submitAudit('2')" :loading="auditLoading">拒 绝</el-button>
          <el-button type="success" @click="submitAudit('1')" :loading="auditLoading">通 过</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { listManageUsers, addManageStudent, addManageTeacher, updateManageUser, deleteManageUser, auditManageUser } from "@/api/edu/audit"
import { listDept } from "@/api/system/dept"
import useUserStore from '@/store/modules/user'
import { ElMessage, ElMessageBox } from "element-plus"

const { proxy } = getCurrentInstance()
const userStore = useUserStore()

const userList = ref([])
const loading = ref(false)
const showSearch = ref(true)
const total = ref(0)
const submitLoading = ref(false)
const auditLoading = ref(false)

const deptOptions = ref([])

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  nickName: undefined,
  classId: undefined,
  studentNo: undefined,
  auditStatus: undefined,
  applyRole: undefined
})

// 是否为管理员
const isAdmin = computed(() => userStore.roles.includes('admin'))
// 是否为教师
const isTeacher = computed(() => userStore.roles.includes('teacher'))

// ==================== 列表查询 ====================

function getDeptList() {
  listDept().then(res => {
    deptOptions.value = res.data || []
  })
}

function getList() {
  loading.value = true
  listManageUsers(queryParams.value).then(res => {
    userList.value = res.rows
    total.value = res.total
    loading.value = false
  }).catch(() => {
    loading.value = false
  })
}

function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

function resetQuery() {
  queryParams.value = {
    pageNum: 1,
    pageSize: 10,
    nickName: undefined,
    classId: undefined,
    studentNo: undefined,
    auditStatus: undefined,
    applyRole: undefined
  }
  getList()
}

// ==================== 新增 ====================

const addDialogVisible = ref(false)
const addActiveTab = ref("student")
const addFormRef = ref(null)

const addForm = ref({
  studentNo: "",
  teacherNo: "",
  nickName: "",
  email: "",
  password: "",
  confirmPassword: "",
  major: "",
  grade: "",
  title: "",
  researchArea: ""
})

const equalToPassword = (rule, value, callback) => {
  if (addForm.value.password !== value) {
    callback(new Error("两次输入的密码不一致"))
  } else {
    callback()
  }
}

const addBaseRules = {
  nickName: [
    { required: true, trigger: "blur", message: "请输入姓名" },
    { max: 30, message: "姓名长度不能超过30个字符", trigger: "blur" }
  ],
  email: [
    { required: true, trigger: "blur", message: "请输入邮箱" },
    { type: "email", message: "请输入正确的邮箱格式", trigger: "blur" },
    { max: 50, message: "邮箱长度不能超过50个字符", trigger: "blur" }
  ],
  password: [
    { required: true, trigger: "blur", message: "请输入密码" },
    { min: 5, max: 20, message: "密码长度必须介于 5 和 20 之间", trigger: "blur" },
    { pattern: /^[^<>"'|\\]+$/, message: "不能包含非法字符：< > \" ' \\ |", trigger: "blur" }
  ],
  confirmPassword: [
    { required: true, trigger: "blur", message: "请再次输入密码" },
    { required: true, validator: equalToPassword, trigger: "blur" }
  ]
}

const addStudentRules = {
  studentNo: [
    { required: true, trigger: "blur", message: "请输入学号" },
    { max: 30, message: "学号长度不能超过30个字符", trigger: "blur" }
  ]
}

const addTeacherRules = {
  teacherNo: [
    { required: true, trigger: "blur", message: "请输入教师编号" },
    { max: 30, message: "教师编号长度不能超过30个字符", trigger: "blur" }
  ]
}

const addRules = computed(() => {
  const roleRules = addActiveTab.value === 'student' ? addStudentRules : addTeacherRules
  return { ...addBaseRules, ...roleRules }
})

function resetAddForm() {
  addForm.value = {
    studentNo: "",
    teacherNo: "",
    nickName: "",
    email: "",
    password: "",
    confirmPassword: "",
    major: "",
    grade: "",
    title: "",
    researchArea: ""
  }
}

function handleAdd() {
  addActiveTab.value = "student"
  resetAddForm()
  addDialogVisible.value = true
}

function handleAddTabChange() {
  proxy.$refs.addFormRef && proxy.$refs.addFormRef.clearValidate()
}

function submitAdd() {
  proxy.$refs.addFormRef.validate(valid => {
    if (valid) {
      submitLoading.value = true
      const isStudent = addActiveTab.value === 'student'
      const f = addForm.value
      const formData = isStudent ? {
        studentNo: f.studentNo,
        nickName: f.nickName,
        email: f.email,
        password: f.password,
        confirmPassword: f.confirmPassword,
        major: f.major,
        grade: f.grade
      } : {
        teacherNo: f.teacherNo,
        nickName: f.nickName,
        email: f.email,
        password: f.password,
        confirmPassword: f.confirmPassword,
        title: f.title,
        researchArea: f.researchArea
      }
      const api = isStudent ? addManageStudent : addManageTeacher
      api(formData).then(() => {
        ElMessage.success("新增成功")
        addDialogVisible.value = false
        getList()
      }).finally(() => {
        submitLoading.value = false
      })
    }
  })
}

// ==================== 编辑 ====================

const editDialogVisible = ref(false)
const editFormRef = ref(null)

const editForm = ref({
  userId: undefined,
  applyRole: "",
  studentNo: "",
  teacherNo: "",
  deptName: "",
  nickName: "",
  email: "",
  phonenumber: "",
  sex: "",
  major: "",
  grade: "",
  title: "",
  researchArea: ""
})

const editRules = {
  nickName: [
    { required: true, trigger: "blur", message: "请输入姓名" },
    { max: 30, message: "姓名长度不能超过30个字符", trigger: "blur" }
  ],
  email: [
    { required: true, trigger: "blur", message: "请输入邮箱" },
    { type: "email", message: "请输入正确的邮箱格式", trigger: "blur" },
    { max: 50, message: "邮箱长度不能超过50个字符", trigger: "blur" }
  ]
}

function handleUpdate(row) {
  editForm.value = {
    userId: row.userId,
    applyRole: row.applyRole,
    studentNo: row.studentNo || "",
    teacherNo: row.teacherNo || "",
    deptName: row.deptName || "",
    nickName: row.nickName || "",
    email: row.email || "",
    phonenumber: row.phonenumber || "",
    sex: row.sex || "0",
    major: row.major || "",
    grade: row.grade || "",
    title: row.title || "",
    researchArea: row.researchArea || ""
  }
  editDialogVisible.value = true
}

function submitEdit() {
  proxy.$refs.editFormRef.validate(valid => {
    if (valid) {
      submitLoading.value = true
      const f = editForm.value
      const data = {
        nickName: f.nickName,
        email: f.email,
        phonenumber: f.phonenumber,
        sex: f.sex
      }
      if (f.applyRole === 'student') {
        data.major = f.major
        data.grade = f.grade
      } else {
        data.title = f.title
        data.researchArea = f.researchArea
      }
      updateManageUser(f.userId, data).then(() => {
        ElMessage.success("更新成功")
        editDialogVisible.value = false
        getList()
      }).finally(() => {
        submitLoading.value = false
      })
    }
  })
}

// ==================== 删除 ====================

function handleDelete(row) {
  const tipText = isAdmin.value
    ? '将停用该用户，确定要移除该用户吗？'
    : '将该学生从您的班级中移除，学生信息不会删除。确定要移除该用户吗？'
  ElMessageBox.confirm(tipText, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    return deleteManageUser(row.userId)
  }).then(() => {
    ElMessage.success("操作成功")
    getList()
  }).catch(() => {})
}

// ==================== 审核 ====================

const auditDialogVisible = ref(false)
const auditFormRef = ref(null)
const auditRow = ref({})

const auditForm = ref({
  auditRemark: ""
})

const auditRules = {
  auditRemark: [
    { max: 200, message: "备注长度不能超过200个字符", trigger: "blur" }
  ]
}

function handleAudit(row) {
  auditRow.value = { ...row }
  auditForm.value = { auditRemark: "" }
  auditDialogVisible.value = true
}

function submitAudit(auditStatus) {
  // 拒绝时校验拒绝原因
  if (auditStatus === '2' && !auditForm.value.auditRemark) {
    ElMessage.warning("请填写拒绝原因")
    return
  }
  auditLoading.value = true
  auditManageUser(auditRow.value.userId, {
    auditStatus,
    auditRemark: auditForm.value.auditRemark
  }).then(() => {
    ElMessage.success(auditStatus === '1' ? "审核通过" : "已拒绝")
    auditDialogVisible.value = false
    getList()
  }).finally(() => {
    auditLoading.value = false
  })
}

getDeptList()
getList()
</script>
