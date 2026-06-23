<template>
  <div class="activity-wall">
    <div
      class="wall-body"
      :style="{ height: bodyHeight + 'px' }"
      v-if="activities.length"
      @mouseenter="pause"
      @mouseleave="resume"
    >
      <div
        class="wall-track"
        :style="{ transform: `translateY(-${offset}px)`, transition: transitionStyle }"
      >
        <div v-for="(item, idx) in displayList" :key="idx" class="wall-item">
          <span class="wall-actor" :title="`查看 ${item.actor_name} 的名片`" @click="showCard(item)">
            {{ item.actor_name }}
          </span>
          <span class="wall-action">
            在<span class="wall-task" :title="`打开课题：${item.task_name}`" @click="openTask(item)">
              《{{ item.task_name }}》
            </span>{{ item.action_label }}
          </span>
          <span class="wall-time" :title="item.occurred_at">{{ item.occurred_at_label }}</span>
        </div>
      </div>
    </div>
    <div class="wall-empty" :style="{ height: bodyHeight + 'px' }" v-else>
      {{ loading ? '加载中...' : '暂无动态' }}
    </div>

    <!-- 用户名片弹窗 -->
    <el-dialog v-model="cardVisible" :title="cardData?.nick_name ? `${cardData.nick_name} 的名片` : '用户名片'" width="360px" append-to-body>
      <div v-loading="cardLoading" class="user-card">
        <template v-if="cardData">
          <div class="card-row"><span class="card-label">姓名</span><span class="card-value">{{ cardData.nick_name || '-' }}</span></div>
          <div class="card-row"><span class="card-label">角色</span><span class="card-value">{{ cardData.role_name || '-' }}</span></div>
          <div class="card-row" v-if="cardData.class_name"><span class="card-label">班级</span><span class="card-value">{{ cardData.class_name }}</span></div>
          <div class="card-row" v-if="cardData.major"><span class="card-label">专业</span><span class="card-value">{{ cardData.major }}</span></div>
          <div class="card-row" v-if="cardData.title"><span class="card-label">职称</span><span class="card-value">{{ cardData.title }}</span></div>
          <div class="card-row"><span class="card-label">注册时间</span><span class="card-value">{{ cardData.create_time || '-' }}</span></div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { getRecentActivities, getUserCard, checkTaskAccess } from '@/api/learning/activity'
import { useIntervalFn } from '@vueuse/core'
import { ElMessage } from 'element-plus'

// 首页"动态"卡片：登录后展示最近操作，可视区固定 visibleRows 行，超出无缝上滚
// 人名可点击弹出名片；课题可点击，后端校验数据权限后跳转到对应任务列表页
const props = defineProps({
  limit: { type: Number, default: 20 },
  visibleRows: { type: Number, default: 8 },
})

const router = useRouter()

const ROW_HEIGHT = 48
const SCROLL_INTERVAL = 2500
const TRANSITION_MS = 500

const bodyHeight = computed(() => props.visibleRows * ROW_HEIGHT)

const activities = ref([])
const offset = ref(0)
const transitionOn = ref(true)
const loading = ref(true)

const shouldScroll = computed(() => activities.value.length > props.visibleRows)
const displayList = computed(() =>
  activities.value.length ? activities.value.concat(activities.value) : []
)
const transitionStyle = computed(() => (transitionOn.value ? `transform ${TRANSITION_MS}ms ease` : 'none'))

function step() {
  if (!shouldScroll.value) {
    offset.value = 0
    return
  }
  offset.value += ROW_HEIGHT
  if (offset.value >= activities.value.length * ROW_HEIGHT) {
    setTimeout(() => {
      transitionOn.value = false
      offset.value = 0
      nextTick(() => { transitionOn.value = true })
    }, TRANSITION_MS)
  }
}
const { pause, resume } = useIntervalFn(step, SCROLL_INTERVAL)

// 人名 → 弹出名片
const cardVisible = ref(false)
const cardLoading = ref(false)
const cardData = ref(null)
async function showCard(item) {
  if (!item.actor_id) {
    ElMessage.warning('该用户信息暂不可查')
    return
  }
  cardVisible.value = true
  cardLoading.value = true
  cardData.value = null
  try {
    const res = await getUserCard(item.actor_id)
    cardData.value = res?.data || null
    if (!cardData.value) {
      ElMessage.warning('未找到该用户信息')
      cardVisible.value = false
    }
  } catch (e) {
    cardVisible.value = false
  } finally {
    cardLoading.value = false
  }
}

// 课题 → 后端校验数据权限后跳转
async function openTask(item) {
  if (!item.task_id) {
    ElMessage.warning('该课题信息暂不可查')
    return
  }
  try {
    const res = await checkTaskAccess(item.task_id)
    const data = res?.data || {}
    if (data.can_access && data.redirect_path) {
      router.push(data.redirect_path)
    } else {
      ElMessage.warning(data.reason || '您无权访问该课题')
    }
  } catch (e) {
    // 错误提示已由 request 拦截器统一处理
  }
}

async function load() {
  loading.value = true
  try {
    const res = await getRecentActivities(props.limit)
    activities.value = res?.data || []
    offset.value = 0
  } catch (e) {
    activities.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="less">
.activity-wall {
  padding: 0 16px 8px 16px;
}
.wall-body {
  overflow: hidden;
}
.wall-item {
  height: 48px;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 1px dashed var(--el-border-color-lighter);
  font-size: 14px;
}
.wall-actor {
  color: var(--el-color-primary);
  font-weight: 600;
  flex-shrink: 0;
  max-width: 80px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  cursor: pointer;
  &:hover {
    color: var(--el-color-primary-light-3);
    text-decoration: underline;
  }
}
.wall-action {
  flex: 1;
  color: var(--el-text-color-regular);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.wall-task {
  color: var(--el-color-primary);
  margin: 0 2px;
  cursor: pointer;
  &:hover {
    color: var(--el-color-primary-light-3);
    text-decoration: underline;
  }
}
.wall-time {
  flex-shrink: 0;
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}
.wall-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

/* 用户名片 */
.user-card {
  min-height: 60px;
  .card-row {
    display: flex;
    padding: 8px 0;
    border-bottom: 1px dashed var(--el-border-color-lighter);
    &:last-child {
      border-bottom: none;
    }
  }
  .card-label {
    flex: 0 0 80px;
    color: var(--el-text-color-secondary);
  }
  .card-value {
    flex: 1;
    color: var(--el-text-color-primary);
    font-weight: 500;
  }
}
</style>
