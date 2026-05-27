<template>
  <div class="register">
    <el-form ref="registerRef" :model="registerForm" :rules="registerRules" class="register-form">
      <h3 class="title">{{ title }}</h3>

      <el-alert
        v-if="!registerEnabled"
        title="注册程序已关闭，禁止注册"
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 15px"
      />

      <!-- 角色切换 -->
      <el-tabs v-model="activeRole" class="register-tabs" @tab-change="handleRoleChange">
        <el-tab-pane name="student">
          <template #label>
            <span :class="['role-tab', 'role-student', { active: activeRole === 'student' }]">学生注册</span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="teacher">
          <template #label>
            <span :class="['role-tab', 'role-teacher', { active: activeRole === 'teacher' }]">教师注册</span>
          </template>
        </el-tab-pane>
      </el-tabs>

      <!-- 学生：学号 -->
      <el-form-item v-if="activeRole === 'student'" prop="studentNo">
        <el-input
          v-model="registerForm.studentNo"
          type="text"
          size="large"
          auto-complete="off"
          placeholder="学号（登录账号）"
        >
          <template #prefix><svg-icon icon-class="user" class="el-input__icon input-icon" /></template>
        </el-input>
      </el-form-item>

      <!-- 教师：教师编号 -->
      <el-form-item v-if="activeRole === 'teacher'" prop="teacherNo">
        <el-input
          v-model="registerForm.teacherNo"
          type="text"
          size="large"
          auto-complete="off"
          placeholder="教师编号（登录账号）"
        >
          <template #prefix><svg-icon icon-class="user" class="el-input__icon input-icon" /></template>
        </el-input>
      </el-form-item>

      <!-- 昵称/姓名 -->
      <el-form-item prop="nickName">
        <el-input
          v-model="registerForm.nickName"
          type="text"
          size="large"
          auto-complete="off"
          :placeholder="activeRole === 'student' ? '学生姓名' : '教师姓名'"
        >
          <template #prefix><svg-icon icon-class="peoples" class="el-input__icon input-icon" /></template>
        </el-input>
      </el-form-item>

      <!-- 邮箱 -->
      <el-form-item prop="email">
        <el-input
          v-model="registerForm.email"
          type="text"
          size="large"
          auto-complete="off"
          placeholder="邮箱"
        >
          <template #prefix><svg-icon icon-class="email" class="el-input__icon input-icon" /></template>
        </el-input>
      </el-form-item>

      <!-- 密码 -->
      <el-form-item prop="password">
        <el-input
          v-model="registerForm.password"
          type="password"
          size="large"
          auto-complete="off"
          placeholder="密码"
          @keyup.enter="handleRegister"
        >
          <template #prefix><svg-icon icon-class="password" class="el-input__icon input-icon" /></template>
        </el-input>
      </el-form-item>

      <!-- 确认密码 -->
      <el-form-item prop="confirmPassword">
        <el-input
          v-model="registerForm.confirmPassword"
          type="password"
          size="large"
          auto-complete="off"
          placeholder="确认密码"
          @keyup.enter="handleRegister"
        >
          <template #prefix><svg-icon icon-class="password" class="el-input__icon input-icon" /></template>
        </el-input>
      </el-form-item>

      <!-- 学生：专业 -->
      <el-form-item v-if="activeRole === 'student'" prop="major">
        <el-input
          v-model="registerForm.major"
          type="text"
          size="large"
          auto-complete="off"
          placeholder="专业（选填）"
        >
          <template #prefix><svg-icon icon-class="education" class="el-input__icon input-icon" /></template>
        </el-input>
      </el-form-item>

      <!-- 学生：年级 -->
      <el-form-item v-if="activeRole === 'student'" prop="grade">
        <el-input
          v-model="registerForm.grade"
          type="text"
          size="large"
          auto-complete="off"
          placeholder="年级（选填）"
        >
          <template #prefix><svg-icon icon-class="date" class="el-input__icon input-icon" /></template>
        </el-input>
      </el-form-item>

      <!-- 教师：职称 -->
      <el-form-item v-if="activeRole === 'teacher'" prop="title">
        <el-input
          v-model="registerForm.title"
          type="text"
          size="large"
          auto-complete="off"
          placeholder="职称（选填，如：教授、副教授、讲师）"
        >
          <template #prefix><svg-icon icon-class="education" class="el-input__icon input-icon" /></template>
        </el-input>
      </el-form-item>

      <!-- 教师：研究方向 -->
      <el-form-item v-if="activeRole === 'teacher'" prop="researchArea">
        <el-input
          v-model="registerForm.researchArea"
          type="text"
          size="large"
          auto-complete="off"
          placeholder="研究方向（选填）"
        >
          <template #prefix><svg-icon icon-class="search" class="el-input__icon input-icon" /></template>
        </el-input>
      </el-form-item>

      <!-- 验证码 -->
      <el-form-item prop="code" v-if="captchaEnabled">
        <el-input
          size="large"
          v-model="registerForm.code"
          auto-complete="off"
          placeholder="验证码"
          style="width: 63%"
          @keyup.enter="handleRegister"
        >
          <template #prefix><svg-icon icon-class="validCode" class="el-input__icon input-icon" /></template>
        </el-input>
        <div class="register-code">
          <img :src="codeUrl" @click="getCode" class="register-code-img"/>
        </div>
      </el-form-item>

      <el-form-item style="width:100%;">
        <el-button
          :loading="loading"
          :disabled="!registerEnabled"
          size="large"
          type="primary"
          style="width:100%;"
          @click.prevent="handleRegister"
        >
          <span v-if="!loading">注 册</span>
          <span v-else>注 册 中...</span>
        </el-button>
        <div style="float: right;">
          <router-link class="link-type" :to="'/login'">使用已有账户登录</router-link>
        </div>
      </el-form-item>
    </el-form>
    <!--  底部  -->
    <div class="el-register-footer">
      <span>{{ footerContent }}</span>
    </div>
  </div>
</template>

<script setup>
import { ElMessageBox } from "element-plus"
import { getCodeImg } from "@/api/login"
import { studentRegister, teacherRegister } from "@/api/edu/register"
import defaultSettings from '@/settings'

const title = import.meta.env.VITE_APP_TITLE
const footerContent = defaultSettings.footerContent
const router = useRouter()
const { proxy } = getCurrentInstance()

const activeRole = ref("student")

const registerForm = ref({
  studentNo: "",
  teacherNo: "",
  nickName: "",
  email: "",
  password: "",
  confirmPassword: "",
  code: "",
  uuid: "",
  major: "",
  grade: "",
  title: "",
  researchArea: ""
})

const equalToPassword = (rule, value, callback) => {
  if (registerForm.value.password !== value) {
    callback(new Error("两次输入的密码不一致"))
  } else {
    callback()
  }
}

const baseRules = {
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
  ],
  code: [{ required: true, trigger: "change", message: "请输入验证码" }]
}

const studentRules = {
  studentNo: [
    { required: true, trigger: "blur", message: "请输入学号" },
    { max: 30, message: "学号长度不能超过30个字符", trigger: "blur" }
  ]
}

const teacherRules = {
  teacherNo: [
    { required: true, trigger: "blur", message: "请输入教师编号" },
    { max: 30, message: "教师编号长度不能超过30个字符", trigger: "blur" }
  ]
}

const registerRules = computed(() => {
  const roleRules = activeRole.value === 'student' ? studentRules : teacherRules
  return { ...baseRules, ...roleRules }
})

const codeUrl = ref("")
const loading = ref(false)
const captchaEnabled = ref(true)
const registerEnabled = ref(true)

function handleRoleChange() {
  proxy.$refs.registerRef && proxy.$refs.registerRef.clearValidate()
}

function resetForm() {
  registerForm.value = {
    studentNo: "",
    teacherNo: "",
    nickName: "",
    email: "",
    password: "",
    confirmPassword: "",
    code: "",
    uuid: "",
    major: "",
    grade: "",
    title: "",
    researchArea: ""
  }
}

function handleRegister() {
  proxy.$refs.registerRef.validate(valid => {
    if (valid) {
      loading.value = true
      const isStudent = activeRole.value === 'student'
      const registerApi = isStudent ? studentRegister : teacherRegister

      // 构建请求参数，仅发送当前角色相关字段
      const f = registerForm.value
      const formData = isStudent ? {
        studentNo: f.studentNo,
        nickName: f.nickName,
        email: f.email,
        password: f.password,
        confirmPassword: f.confirmPassword,
        code: f.code,
        uuid: f.uuid,
        major: f.major,
        grade: f.grade
      } : {
        teacherNo: f.teacherNo,
        nickName: f.nickName,
        email: f.email,
        password: f.password,
        confirmPassword: f.confirmPassword,
        code: f.code,
        uuid: f.uuid,
        title: f.title,
        researchArea: f.researchArea
      }

      registerApi(formData).then(res => {
        ElMessageBox.alert(
          "<font color='red'>注册成功，请等待管理员审核！</font>",
          "系统提示",
          {
            dangerouslyUseHTMLString: true,
            type: "success"
          }
        ).then(() => {
          router.push("/login")
        }).catch(() => {})
      }).catch(() => {
        loading.value = false
        if (captchaEnabled.value) {
          getCode()
        }
      })
    }
  })
}

function getCode() {
  getCodeImg().then(res => {
    const payload = res?.data ?? res ?? {}
    captchaEnabled.value = payload.captchaEnabled === undefined ? true : payload.captchaEnabled
    registerEnabled.value = payload.registerEnabled === undefined ? true : payload.registerEnabled
    if (captchaEnabled.value) {
      codeUrl.value = "data:image/gif;base64," + payload.img
      registerForm.value.uuid = payload.uuid
    }
  })
}

getCode()
</script>

<style lang='scss' scoped>
.register {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  background-image: url("../assets/images/login-background.jpg");
  background-size: cover;
}
.title {
  margin: 0px auto 20px auto;
  text-align: center;
  color: #707070;
}

.register-form {
  border-radius: 6px;
  background: #ffffff;
  width: 420px;
  padding: 25px 25px 5px 25px;
  .el-input {
    height: 40px;
    input {
      height: 40px;
    }
  }
  .input-icon {
    height: 39px;
    width: 14px;
    margin-left: 0px;
  }
}

.register-tabs {
  margin-bottom: 14px;
  :deep(.el-tabs__header) {
    margin-bottom: 15px;
  }
  :deep(.el-tabs__nav-wrap::after) {
    height: 0;
  }
  :deep(.el-tabs__active-bar) {
    display: none;
  }
  :deep(.el-tabs__item) {
    padding: 0 6px;
    height: auto;
    line-height: normal;
  }
}

.role-tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 110px;
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 14px;
  border: 1px solid transparent;
  user-select: none;
}

.role-student {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.role-teacher {
  color: var(--el-color-success);
  background: var(--el-color-success-light-9);
  border-color: var(--el-color-success-light-7);
}

.role-student.active {
  color: #fff;
  background: var(--el-color-primary);
  border-color: var(--el-color-primary);
}

.role-teacher.active {
  color: #fff;
  background: var(--el-color-success);
  border-color: var(--el-color-success);
}

.register-tip {
  font-size: 13px;
  text-align: center;
  color: #bfbfbf;
}
.register-code {
  width: 33%;
  height: 40px;
  float: right;
  img {
    cursor: pointer;
    vertical-align: middle;
  }
}
.el-register-footer {
  height: 40px;
  line-height: 40px;
  position: fixed;
  bottom: 0;
  width: 100%;
  text-align: center;
  color: #fff;
  font-family: Arial;
  font-size: 12px;
  letter-spacing: 1px;
}
.register-code-img {
  height: 40px;
  padding-left: 12px;
}
</style>
