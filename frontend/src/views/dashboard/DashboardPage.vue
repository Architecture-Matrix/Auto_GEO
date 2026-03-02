<template>
  <div class="dashboard-page">
    <!-- 系统状态概览 -->
    <div class="section">
      <h2 class="section-title">
        <el-icon><DataAnalysis /></el-icon>
        系统状态概览
      </h2>
      <div class="stats-grid">
        <div class="stat-card" @click="goTo('/clients')">
          <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
            <el-icon><UserFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.clients }}</div>
            <div class="stat-label">客户总数</div>
          </div>
        </div>
        <div class="stat-card" @click="goTo('/knowledge')">
          <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
            <el-icon><Reading /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.knowledgeFiles }}</div>
            <div class="stat-label">知识库文件</div>
          </div>
        </div>
        <div class="stat-card" @click="goTo('/geo/keywords')">
          <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
            <el-icon><MagicStick /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.keywords }}</div>
            <div class="stat-label">关键词数量</div>
          </div>
        </div>
        <div class="stat-card" @click="goTo('/geo/articles')">
          <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.articles }}</div>
            <div class="stat-label">生成文章</div>
          </div>
        </div>
        <div class="stat-card" @click="goTo('/accounts')">
          <div class="stat-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%)">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.accounts }}</div>
            <div class="stat-label">授权账号</div>
          </div>
        </div>
        <div class="stat-card" @click="goTo('/auto-publish')">
          <div class="stat-icon" style="background: linear-gradient(135deg, #30cfd0 0%, #330867 100%)">
            <el-icon><List /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.publishTasks }}</div>
            <div class="stat-label">发布任务</div>
          </div>
        </div>
        <div class="stat-card" @click="goTo('/geo/monitor')">
          <div class="stat-icon" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.indexed }}</div>
            <div class="stat-label">已收录</div>
          </div>
        </div>
        <div class="stat-card" @click="goTo('/data-report')">
          <div class="stat-icon" style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.todayPublished }}</div>
            <div class="stat-label">今日发布</div>
          </div>
        </div>
      </div>
    </div>

    <!-- GEO业务流程 -->
    <div class="section">
      <h2 class="section-title">
        <el-icon><Operation /></el-icon>
        GEO 业务流程
        <span class="section-subtitle">点击卡片跳转到对应功能</span>
      </h2>
      <div class="process-flow">
        <div
          v-for="(step, index) in processSteps"
          :key="step.path"
          class="process-step"
          :class="{ active: step.active }"
          @click="goTo(step.path)"
        >
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-icon">
            <el-icon>
              <component :is="step.icon" />
            </el-icon>
          </div>
          <div class="step-content">
            <div class="step-title">{{ step.title }}</div>
            <div class="step-desc">{{ step.desc }}</div>
          </div>
          <div class="step-arrow" v-if="index < processSteps.length - 1">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- 待办事项 & 快速操作 -->
    <div class="two-columns">
      <!-- 待办事项 -->
      <div class="section">
        <h2 class="section-title">
          <el-icon><Bell /></el-icon>
          待办事项
        </h2>
        <div class="todo-list">
          <div v-if="todos.length === 0" class="empty-todo">
            <el-icon><CircleCheck /></el-icon>
            <span>暂无待办事项</span>
          </div>
          <div v-else class="todo-item" v-for="todo in todos" :key="todo.id" @click="goTo(todo.path)">
            <div class="todo-icon" :class="`todo-${todo.type}`">
              <el-icon><component :is="todo.icon" /></el-icon>
            </div>
            <div class="todo-content">
              <div class="todo-title">{{ todo.title }}</div>
              <div class="todo-desc">{{ todo.desc }}</div>
            </div>
            <div class="todo-count">{{ todo.count }}</div>
          </div>
        </div>
      </div>

      <!-- 快速操作 -->
      <div class="section">
        <h2 class="section-title">
          <el-icon><Lightning /></el-icon>
          快速操作
        </h2>
        <div class="quick-actions">
          <el-button type="primary" size="large" @click="goTo('/clients')">
            <el-icon><Plus /></el-icon>
            新建客户
          </el-button>
          <el-button type="success" size="large" @click="goTo('/accounts/add')">
            <el-icon><User /></el-icon>
            添加账号
          </el-button>
          <el-button type="warning" size="large" @click="goTo('/geo/articles')">
            <el-icon><EditPen /></el-icon>
            生成文章
          </el-button>
          <el-button type="danger" size="large" @click="goTo('/publish')">
            <el-icon><Monitor /></el-icon>
            平台发布监控
          </el-button>
        </div>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="section">
      <h2 class="section-title">
        <el-icon><Clock /></el-icon>
        最近活动
      </h2>
      <el-table :data="recentActivities" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getActivityTypeColor(row.type)">{{ row.typeText }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="platform" label="平台" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.platform" :color="getPlatformColor(row.platform)" effect="dark">
              {{ getPlatformName(row.platform) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.statusText }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="time" label="时间" width="180" />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  DataAnalysis, UserFilled, Reading, MagicStick, Document, User, List,
  Monitor, TrendCharts, Operation, ArrowRight, Bell, CircleCheck,
  Lightning, Plus, EditPen, Promotion, Clock, House, Platform,
  Key, FolderOpened, Timer, Setting
} from '@element-plus/icons-vue'
import { clientApi } from '@/services/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)

// 系统统计数据
const stats = ref({
  clients: 0,
  knowledgeFiles: 0,
  keywords: 0,
  articles: 0,
  accounts: 0,
  publishTasks: 0,
  indexed: 0,
  todayPublished: 0
})

// GEO业务流程步骤
const processSteps = ref([
  { title: '客户管理', desc: '创建和管理客户', icon: 'UserFilled', path: '/clients', active: true },
  { title: '知识库管理', desc: '上传和管理知识文档', icon: 'Reading', path: '/knowledge', active: true },
  { title: '智能建站', desc: '配置和生成站点', icon: 'Platform', path: '/site-builder', active: true },
  { title: '关键词蒸馏', desc: 'AI提取优质关键词', icon: 'MagicStick', path: '/geo/keywords', active: true },
  { title: '文章生成', desc: 'AI生成GEO文章', icon: 'EditPen', path: '/geo/articles', active: true },
  { title: '文章管理', desc: '管理和编辑文章', icon: 'Document', path: '/articles', active: true },
  { title: '账号管理', desc: '管理发布账号', icon: 'User', path: '/accounts', active: true },
  { title: '发布任务', desc: '创建和管理发布任务', icon: 'List', path: '/auto-publish', active: true },
  { title: '平台发布监控', desc: '实时监控发布进度', icon: 'Monitor', path: '/publish', active: true },
  { title: '收录监控', desc: '监控文章收录情况', icon: 'DataAnalysis', path: '/geo/monitor', active: true },
  { title: '数据报表', desc: '查看数据分析', icon: 'TrendCharts', path: '/data-report', active: true },
  { title: '定时任务', desc: '配置定时任务', icon: 'Timer', path: '/scheduler', active: true },
  { title: '系统设置', desc: '系统参数配置', icon: 'Setting', path: '/settings', active: true }
])

// 待办事项
const todos = ref<any[]>([])

// 最近活动
const recentActivities = ref([
  {
    type: 'publish',
    typeText: '发布',
    title: '示例文章已发布到知乎',
    platform: 'zhihu',
    status: 'success',
    statusText: '成功',
    time: '2025-01-08 12:00'
  }
])

// 加载系统统计数据
const loadStats = async () => {
  try {
    // 加载客户统计
    const clientStats = await clientApi.getStats()
    stats.value.clients = clientStats.data?.total || 0
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

// 加载待办事项
const loadTodos = async () => {
  // 这里可以从后端API获取实际的待办事项
  todos.value = [
    {
      id: 1,
      type: 'warning',
      icon: 'Document',
      title: '待发布文章',
      desc: '有文章等待发布',
      count: 5,
      path: '/articles'
    },
    {
      id: 2,
      type: 'danger',
      icon: 'User',
      title: '账号待授权',
      desc: '有账号需要重新授权',
      count: 2,
      path: '/accounts'
    }
  ]
}

// 页面跳转
const goTo = (path: string) => {
  router.push(path)
}

// 工具方法
const getActivityTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    publish: 'success',
    generate: 'warning',
    auth: 'danger'
  }
  return colors[type] || 'info'
}

const getPlatformColor = (platform: string) => {
  const colors: Record<string, string> = {
    zhihu: '#0084FF',
    baijiahao: '#E53935',
    sohu: '#FF6B00',
    toutiao: '#333333'
  }
  return colors[platform] || '#666'
}

const getPlatformName = (platform: string) => {
  const names: Record<string, string> = {
    zhihu: '知乎',
    baijiahao: '百家号',
    sohu: '搜狐号',
    toutiao: '头条号'
  }
  return names[platform] || platform
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    success: 'success',
    pending: 'warning',
    failed: 'danger'
  }
  return types[status] || 'info'
}

onMounted(() => {
  loadStats()
  loadTodos()
})
</script>

<style scoped lang="scss">
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 20px;
}

.section {
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 24px;

  .section-title {
    margin: 0 0 20px 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 8px;

    .section-subtitle {
      font-size: 13px;
      font-weight: 400;
      color: var(--text-secondary);
      margin-left: 8px;
    }
  }
}

// 统计卡片网格
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;

  @media (max-width: 1400px) {
    grid-template-columns: repeat(3, 1fr);
  }

  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.1);
      border-color: var(--primary-color);
    }

    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: white;
      flex-shrink: 0;
    }

    .stat-content {
      flex: 1;

      .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
      }

      .stat-label {
        font-size: 13px;
        color: var(--text-secondary);
        margin-top: 4px;
      }
    }
  }
}

// 业务流程
.process-flow {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: stretch;

  .process-step {
    flex: 1;
    min-width: 140px;
    max-width: 180px;
    background: linear-gradient(135deg, rgba(103, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border: 2px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;

    &:hover {
      transform: translateY(-4px);
      border-color: var(--primary-color);
      background: linear-gradient(135deg, rgba(103, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
    }

    .step-number {
      position: absolute;
      top: 8px;
      right: 8px;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--primary-color);
      color: white;
      font-size: 12px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .step-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      background: var(--bg-tertiary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: var(--primary-color);
    }

    .step-content {
      text-align: center;

      .step-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 4px;
      }

      .step-desc {
        font-size: 12px;
        color: var(--text-secondary);
        line-height: 1.4;
      }
    }

    .step-arrow {
      position: absolute;
      right: -20px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 20px;
      color: var(--text-secondary);
      display: none;

      @media (min-width: 1400px) {
        display: block;
      }
    }
  }
}

// 两列布局
.two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

// 待办事项
.todo-list {
  .empty-todo {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 40px 20px;
    color: var(--text-secondary);

    .el-icon {
      font-size: 48px;
      color: var(--success-color);
    }
  }

  .todo-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: 8px;
    background: var(--bg-tertiary);
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 8px;

    &:hover {
      background: rgba(var(--primary-rgb), 0.1);
    }

    .todo-icon {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;

      &.todo-warning {
        background: rgba(255, 152, 0, 0.1);
        color: #ff9800;
      }

      &.todo-danger {
        background: rgba(244, 67, 54, 0.1);
        color: #f44336;
      }
    }

    .todo-content {
      flex: 1;

      .todo-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--text-primary);
      }

      .todo-desc {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 2px;
      }
    }

    .todo-count {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: var(--primary-color);
      color: white;
      font-size: 12px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}

// 快速操作
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .el-button {
    width: 100%;
    justify-content: flex-start;
    padding: 16px 20px;

    .el-icon {
      font-size: 18px;
    }
  }
}

// 表格样式覆盖
:deep(.el-table) {
  background: transparent;
  color: var(--text-primary);

  .el-table__header {
    th {
      background: var(--bg-tertiary);
      color: var(--text-secondary);
    }
  }

  .el-table__body {
    tr {
      background: transparent;

      &:hover td {
        background: var(--bg-tertiary);
      }
    }

    td {
      border-color: var(--border);
    }
  }
}
</style>
