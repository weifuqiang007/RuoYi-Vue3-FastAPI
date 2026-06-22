<template>
   <div class="app-container">
      <el-row :gutter="20">
         <el-col :span="6" :xs="24">
            <el-card class="box-card">
               <template v-slot:header>
                 <div class="clearfix">
                   <span>个人信息</span>
                 </div>
               </template>
               <div>
                  <div class="text-center">
                     <userAvatar />
                  </div>
                  <ul class="list-group list-group-striped">
                     <li class="list-group-item">
                        <svg-icon icon-class="user" />用户名称
                        <div class="pull-right">{{ state.user.userName }}</div>
                     </li>
                     <li class="list-group-item">
                        <svg-icon icon-class="phone" />手机号码
                        <div class="pull-right">{{ state.user.phonenumber }}</div>
                     </li>
                     <li class="list-group-item">
                        <svg-icon icon-class="email" />用户邮箱
                        <div class="pull-right">{{ state.user.email }}</div>
                     </li>
                     <li class="list-group-item">
                        <svg-icon icon-class="tree" />所属部门
                        <div class="pull-right class-cards">
                           <span v-if="!classCards.length" class="class-empty">未设置</span>
                           <div v-for="c in classCards" :key="c.classId" class="class-card">
                              <svg-icon icon-class="tree" class="class-card-icon" />
                              <span>{{ c.deptName }}</span>
                           </div>
                        </div>
                     </li>
                     <li class="list-group-item">
                        <svg-icon icon-class="peoples" />所属角色
                        <div class="pull-right">{{ state.roleGroup }}</div>
                     </li>
                     <li class="list-group-item">
                        <svg-icon icon-class="date" />创建日期
                        <div class="pull-right">{{ state.user.createTime }}</div>
                     </li>
                  </ul>
               </div>
            </el-card>
         </el-col>
         <el-col :span="18" :xs="24">
            <el-card>
               <template v-slot:header>
                 <div class="clearfix">
                   <span>基本资料</span>
                 </div>
               </template>
               <el-tabs v-model="selectedTab">
                  <el-tab-pane label="基本资料" name="userinfo">
                     <userInfo :user="state.user" />
                  </el-tab-pane>
                  <el-tab-pane label="修改密码" name="resetPwd">
                     <resetPwd />
                  </el-tab-pane>
                  <el-tab-pane label="所属班级" name="myclass">
                     <userClass :user="state.user" @refresh="getUser" />
                  </el-tab-pane>
               </el-tabs>
            </el-card>
         </el-col>
      </el-row>
   </div>
</template>

<script setup name="Profile">
import userAvatar from "./userAvatar";
import userInfo from "./userInfo";
import resetPwd from "./resetPwd";
import userClass from "./userClass";
import { getUserProfile } from "@/api/system/user";
import useUserStore from "@/store/modules/user";
import { getMyTeacherClasses } from "@/api/edu/profile";

const route = useRoute()
const userStore = useUserStore()
const isTeacher = computed(() => (userStore.roles || []).includes('teacher'))
const classCards = computed(() => {
  if (isTeacher.value) {
    return state.teacherClasses || []
  }
  const dept = state.user && state.user.dept
  return dept && dept.deptName ? [{ classId: dept.deptId, deptName: dept.deptName }] : []
})
const selectedTab = ref("userinfo")
const state = reactive({
  user: {},
  roleGroup: {},
  postGroup: {},
  teacherClasses: []
});

function getUser() {
  getUserProfile().then(response => {
    state.user = response.data;
    state.roleGroup = response.roleGroup;
    state.postGroup = response.postGroup;
    if (isTeacher.value) {
      loadTeacherClasses();
    }
  });
};

function loadTeacherClasses() {
  getMyTeacherClasses().then(res => {
    const list = res.data || []
    state.teacherClasses = list
      .map(item => ({ classId: item.class_id ?? item.classId, deptName: item.dept_name ?? item.deptName }))
      .filter(c => c.deptName)
  });
}

onMounted(() => {
  const activeTab = route.params && route.params.activeTab
  if (activeTab) {
    selectedTab.value = activeTab
  }
  getUser()
})
</script>

<style scoped>
.class-cards {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}
.class-card {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-left: 3px solid #409eff;
  border-radius: 6px;
  padding: 5px 12px;
  font-size: 13px;
  color: #303133;
  line-height: 1.4;
}
.class-card-icon {
  color: #409eff;
}
.class-empty {
  color: #909399;
  font-size: 13px;
}
</style>
