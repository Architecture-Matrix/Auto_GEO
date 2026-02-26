/**
 * 路由配置
 * 定义应用所有路由和侧边栏菜单结构
 */

import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'

// 路由定义
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/views/layout/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      // 侧边栏菜单按业务流程排序：
      // 首页、客户管理、知识库管理、智能建站、关键词蒸馏、文章生成、文章管理、账号管理、批量发布、发布记录、收录监控、数据报表、定时任务、系统设置

      // 1. 首页
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardPage.vue'),
        meta: { title: '首页', icon: 'House', order: 1 },
      },

      // 2. 客户管理
      {
        path: 'clients',
        name: 'Clients',
        component: () => import('@/views/client/ClientPage.vue'),
        meta: { title: '客户管理', icon: 'UserFilled', order: 2 },
      },

      // 3. 知识库管理
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/knowledge/KnowledgePage.vue'),
        meta: { title: '知识库管理', icon: 'Reading', order: 3 },
      },

      // 4. 智能建站
      {
        path: 'site-builder',
        name: 'SiteBuilder',
        component: () => import('@/views/site-builder/ConfigWizard.vue'),
        meta: { title: '智能建站', icon: 'Platform', order: 4 },
      },

      // 5. 关键词蒸馏
      {
        path: 'geo/keywords',
        name: 'GeoKeywords',
        component: () => import('@/views/geo/Keywords.vue'),
        meta: { title: '关键词蒸馏', icon: 'MagicStick', order: 5 },
      },

      // 6. 文章生成
      {
        path: 'geo/articles',
        name: 'GeoArticles',
        component: () => import('@/views/geo/Articles.vue'),
        meta: { title: '文章生成', icon: 'EditPen', order: 6 },
      },

      // 7. 文章管理
      {
        path: 'articles',
        name: 'Articles',
        component: () => import('@/views/article/ArticleList.vue'),
        meta: { title: '文章管理', icon: 'Document', order: 7 },
      },
      {
        path: 'articles/add',
        name: 'ArticleAdd',
        component: () => import('@/views/article/ArticleEdit.vue'),
        meta: { title: '新建文章', hidden: true },
      },
      {
        path: 'articles/edit/:id',
        name: 'ArticleEdit',
        component: () => import('@/views/article/ArticleEdit.vue'),
        meta: { title: '编辑文章', hidden: true },
      },

      // 8. 账号管理
      {
        path: 'accounts',
        name: 'Accounts',
        component: () => import('@/views/account/AccountList.vue'),
        meta: { title: '账号管理', icon: 'User', order: 8 },
      },
      {
        path: 'accounts/add',
        name: 'AccountAdd',
        component: () => import('@/views/account/AccountAdd.vue'),
        meta: { title: '添加账号', hidden: true },
      },

      // 9. 批量发布
      {
        path: 'publish',
        name: 'Publish',
        component: () => import('@/views/publish/PublishPage.vue'),
        meta: { title: '批量发布', icon: 'Promotion', order: 9 },
      },

      // 10. 发布记录
      {
        path: 'history',
        name: 'History',
        component: () => import('@/views/publish/PublishHistory.vue'),
        meta: { title: '发布记录', icon: 'Clock', order: 10 },
      },

      // 11. 收录监控
      {
        path: 'geo/monitor',
        name: 'GeoMonitor',
        component: () => import('@/views/geo/Monitor.vue'),
        meta: { title: '收录监控', icon: 'Monitor', order: 11 },
      },

      // 12. 数据报表
      {
        path: 'data-report',
        name: 'DataReport',
        component: () => import('@/views/report/DataReport.vue'),
        meta: { title: '数据报表', icon: 'DataAnalysis', order: 12 },
      },

      // 13. 定时任务
      {
        path: 'scheduler',
        name: 'Scheduler',
        component: () => import('@/views/scheduler/SchedulerPage.vue'),
        meta: { title: '定时任务', icon: 'Timer', order: 13 },
      },

      // 14. 系统设置
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/SettingsPage.vue'),
        meta: { title: '系统设置', icon: 'Setting', order: 14 },
      },

      // ========== 以下是不在侧边栏显示的辅助路由 ==========
      // GEO项目管理（暂不显示在侧边栏）
      {
        path: 'geo/projects',
        name: 'GeoProjects',
        component: () => import('@/views/geo/Projects.vue'),
        meta: { title: 'GEO项目管理', icon: 'Grid', hidden: true },
      },
      // GEO数据概览（已废弃，保留路由以免报错）
      {
        path: 'geo/dashboard',
        name: 'GeoDashboard',
        component: () => import('@/views/geo/Dashboard.vue'),
        meta: { title: '数据概览', icon: 'PieChart', hidden: true },
      },
    ],
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - AutoGeo`
  }
  next()
})

export default router