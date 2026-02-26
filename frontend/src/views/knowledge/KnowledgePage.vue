<template>
  <div class="knowledge-page">
    <!-- 头部 -->
    <header class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
          </svg>
        </div>
        <div class="header-text">
          <h1 class="page-title">知识库管理</h1>
          <p class="page-desc">企业知识库分类管理，支持多企业隔离存储</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" size="large" @click="showCreateCategory = true">
          <svg viewBox="0 0 16 16" fill="currentColor" width="16">
            <path d="M8 4a.5.5 0 01.5.5v3h3a.5.5 0 010 1h-3v3a.5.5 0 01-1 0v-3h-3a.5.5 0 010-1h3v-3A.5.5 0 018 4z"/>
          </svg>
          新建企业分类
        </el-button>
      </div>
    </header>

    <!-- 企业分类网格 -->
    <section class="categories-section">
      <div class="section-header">
        <h2 class="section-title">企业知识库</h2>
        <div class="section-actions">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索企业或知识..."
            prefix-icon="Search"
            style="width: 260px"
            clearable
          />
        </div>
      </div>

      <div v-loading="loading" class="categories-grid">
        <!-- 企业分类卡片 -->
        <div
          v-for="category in filteredCategories"
          :key="category.id"
          class="category-card"
          @click="viewCategory(category)"
        >
          <div class="card-header">
            <div class="company-info">
              <div class="company-avatar" :style="{ background: category.color }">
                {{ category.initial }}
              </div>
              <div class="company-details">
                <h3 class="company-name">{{ category.name }}</h3>
                <span class="company-industry">{{ category.industry }}</span>
              </div>
            </div>
            <el-dropdown trigger="click" @click.stop>
              <div class="more-btn">
                <svg viewBox="0 0 16 16" fill="currentColor" width="16">
                  <path d="M3 9.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm5 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm5 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3z"/>
                </svg>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="editCategory(category)">
                    <el-icon><Edit /></el-icon>
                    编辑分类
                  </el-dropdown-item>
                  <el-dropdown-item @click="manageKnowledge(category)">
                    <el-icon><Document /></el-icon>
                    管理知识
                  </el-dropdown-item>
                  <el-dropdown-item @click="addKnowledge(category)">
                    <el-icon><Plus /></el-icon>
                    添加知识
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="deleteCategory(category)">
                    <el-icon><Delete /></el-icon>
                    删除分类
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <div class="card-body">
            <p class="company-desc">{{ category.description || '暂无描述' }}</p>

            <!-- 知识统计 -->
            <div class="knowledge-stats">
              <div class="stat-item">
                <svg viewBox="0 0 16 16" fill="currentColor" width="14">
                  <path d="M6.5 2a.5.5 0 01.5.5v1a.5.5 0 01-.5.5h-1a.5.5 0 01-.5-.5v-1a.5.5 0 01.5-.5h1zm3 0a.5.5 0 01.5.5v1a.5.5 0 01-.5.5h-1a.5.5 0 01-.5-.5v-1a.5.5 0 01.5-.5h1z"/>
                </svg>
                <span>{{ category.knowledge_count || 0 }} 条知识</span>
              </div>
              <div class="stat-item">
                <svg viewBox="0 0 16 16" fill="currentColor" width="14">
                  <path d="M8 1a4 4 0 00-4 4v2H2v2h2v6a2 2 0 002 2h4a2 2 0 002-2V9h2V7h-2V5a4 4 0 00-4-4zm0 2a2 2 0 012 2v2H6V5a2 2 0 012-2z"/>
                </svg>
                <span>{{ category.project_count || 0 }} 个关联项目</span>
              </div>
            </div>

            <!-- 标签 -->
            <div class="card-tags">
              <span v-for="tag in category.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>

          <div class="card-footer">
            <span class="update-time">{{ formatTime(category.updated_at) }}</span>
            <button class="action-btn">查看详情</button>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!loading && filteredCategories.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
            </svg>
          </div>
          <h3>还没有企业知识库</h3>
          <p>创建第一个企业分类开始管理知识</p>
          <el-button type="primary" @click="showCreateCategory = true">创建企业分类</el-button>
        </div>
      </div>
    </section>

    <!-- 知识列表抽屉 -->
    <el-drawer
      v-model="showKnowledgeDrawer"
      :title="`知识管理 - ${currentCategory?.name}`"
      size="60%"
      class="knowledge-drawer"
    >
      <div class="drawer-content">
        <div class="drawer-header">
          <div class="search-box">
            <el-input
              v-model="knowledgeSearch"
              placeholder="搜索知识..."
              prefix-icon="Search"
              clearable
            />
          </div>
          <el-button type="primary" @click="showAddKnowledge = true">
            <el-icon><Plus /></el-icon>
            添加知识
          </el-button>
        </div>

        <div v-loading="knowledgeLoading" class="knowledge-list">
          <div
            v-for="item in filteredKnowledge"
            :key="item.id"
            class="knowledge-item"
          >
            <div class="item-header">
              <h4 class="item-title">{{ item.title }}</h4>
              <el-dropdown trigger="click">
                <span class="item-more">···</span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="editKnowledge(item)">
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item @click="deleteKnowledge(item)">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            <p class="item-content">{{ item.content }}</p>
            <div class="item-meta">
              <span class="item-type">{{ item.type }}</span>
              <span class="item-time">{{ formatTime(item.created_at) }}</span>
            </div>
          </div>

          <el-empty v-if="!knowledgeLoading && filteredKnowledge.length === 0" description="暂无知识数据" />
        </div>
      </div>
    </el-drawer>

    <!-- 创建/编辑分类对话框 -->
    <el-dialog
      v-model="showCreateCategory"
      :title="editingCategory ? '编辑企业分类' : '创建企业分类'"
      width="540px"
      :close-on-click-modal="false"
      class="category-dialog"
    >
      <el-form :model="categoryForm" label-position="top">
        <el-form-item label="企业名称" required>
          <el-input
            v-model="categoryForm.name"
            placeholder="如：绿阳环保科技有限公司"
            clearable
            size="large"
          />
        </el-form-item>

        <el-form-item label="所属行业">
          <el-select
            v-model="categoryForm.industry"
            placeholder="选择行业"
            allow-create
            filterable
            style="width: 100%"
            size="large"
          >
            <el-option
              v-for="ind in industries"
              :key="ind"
              :label="ind"
              :value="ind"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="企业描述">
          <el-input
            v-model="categoryForm.description"
            type="textarea"
            :rows="3"
            placeholder="简要描述企业业务范围"
          />
        </el-form-item>

        <el-form-item label="标签">
          <el-input
            v-model="categoryForm.tagsInput"
            placeholder="输入标签，用逗号分隔"
          />
          <div class="form-tip">如：环保, 清洁服务, 无人机</div>
        </el-form-item>

        <el-form-item label="主题颜色">
          <div class="color-picker">
            <div
              v-for="color in presetColors"
              :key="color"
              class="color-option"
              :class="{ active: categoryForm.color === color }"
              :style="{ background: color }"
              @click="categoryForm.color = color"
            />
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateCategory = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveCategory">
          {{ editingCategory ? '保存修改' : '创建分类' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑知识对话框 -->
    <el-dialog
      v-model="showAddKnowledge"
      :title="editingKnowledge ? '编辑知识' : '添加知识'"
      width="540px"
      :close-on-click-modal="false"
      class="knowledge-dialog"
    >
      <el-form :model="knowledgeForm" label-position="top">
        <el-form-item label="知识标题" required>
          <el-input
            v-model="knowledgeForm.title"
            placeholder="如：企业优势介绍"
            clearable
            size="large"
          />
        </el-form-item>

        <el-form-item label="知识类型">
          <el-select v-model="knowledgeForm.type" style="width: 100%" size="large">
            <el-option label="企业介绍" value="company_intro" />
            <el-option label="产品服务" value="product" />
            <el-option label="行业知识" value="industry" />
            <el-option label="常见问题" value="faq" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="知识内容" required>
          <el-input
            v-model="knowledgeForm.content"
            type="textarea"
            :rows="6"
            placeholder="输入详细的知识内容..."
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddKnowledge = false">取消</el-button>
        <el-button type="primary" :loading="savingKnowledge" @click="saveKnowledge">
          {{ editingKnowledge ? '保存修改' : '添加知识' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete, Plus, Document, Search } from '@element-plus/icons-vue'

// ==================== 类型定义 ====================
interface Category {
  id: number
  name: string
  industry?: string
  description?: string
  tags?: string[]
  color: string
  initial: string
  knowledge_count?: number
  project_count?: number
  updated_at: string
  created_at: string
}

interface Knowledge {
  id: number
  title: string
  content: string
  type: string
  category_id: number
  created_at: string
}

// ==================== 状态 ====================
const loading = ref(false)
const saving = ref(false)
const knowledgeLoading = ref(false)
const savingKnowledge = ref(false)

const searchKeyword = ref('')
const knowledgeSearch = ref('')

const categories = ref<Category[]>([])
const knowledges = ref<Knowledge[]>([])

const showCreateCategory = ref(false)
const showKnowledgeDrawer = ref(false)
const showAddKnowledge = ref(false)

const currentCategory = ref<Category | null>(null)
const editingCategory = ref<Category | null>(null)
const editingKnowledge = ref<Knowledge | null>(null)

const categoryForm = ref({
  name: '',
  industry: '',
  description: '',
  tagsInput: '',
  color: '#6366f1',
})

const knowledgeForm = ref({
  title: '',
  type: 'company_intro',
  content: '',
})

// 行业列表
const industries = [
  'SaaS软件',
  '环保工程',
  '工业清洗',
  '无人机服务',
  '电商',
  '教育培训',
  '金融服务',
  '医疗健康',
  '制造业',
  '房地产',
  '餐饮美食',
  '旅游出行',
  '物流运输',
  '新能源',
  '化工行业',
  '建筑工程',
  '其他',
]

// 预设颜色
const presetColors = [
  '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e',
  '#f97316', '#eab308', '#22c55e', '#14b8a6',
  '#06b6d4', '#3b82f6',
]

// ==================== 计算属性 ====================
const filteredCategories = computed(() => {
  if (!searchKeyword.value) return categories.value
  const keyword = searchKeyword.value.toLowerCase()
  return categories.value.filter(c =>
    c.name.toLowerCase().includes(keyword) ||
    c.industry?.toLowerCase().includes(keyword) ||
    c.tags?.some(t => t.toLowerCase().includes(keyword))
  )
})

const filteredKnowledge = computed(() => {
  if (!knowledgeSearch.value) return knowledges.value
  const keyword = knowledgeSearch.value.toLowerCase()
  return knowledges.value.filter(k =>
    k.title.toLowerCase().includes(keyword) ||
    k.content.toLowerCase().includes(keyword)
  )
})

// ==================== 方法 ====================

// 加载企业分类
const loadCategories = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/knowledge/categories')
    if (!response.ok) {
      throw new Error('加载分类失败')
    }
    const data = await response.json()
    categories.value = data.map((cat: any) => ({
      id: cat.id,
      name: cat.name,
      industry: cat.industry,
      description: cat.description,
      tags: cat.tags ? cat.tags.split(',').map((t: string) => t.trim()).filter((t: string) => t) : [],
      color: cat.color,
      initial: cat.name.charAt(0),
      knowledge_count: cat.knowledge_count,
      project_count: cat.project_count,
      updated_at: cat.updated_at,
      created_at: cat.created_at,
    }))
  } catch (error) {
    console.error('加载分类失败:', error)
    ElMessage.error('加载分类失败')
  } finally {
    loading.value = false
  }
}

// 查看分类
const viewCategory = async (category: Category) => {
  await manageKnowledge(category)
}

// 管理知识
const manageKnowledge = async (category: Category) => {
  currentCategory.value = category
  showKnowledgeDrawer.value = true
  await loadKnowledge(category.id)
}

// 加载知识列表
const loadKnowledge = async (categoryId: number) => {
  knowledgeLoading.value = true
  try {
    const response = await fetch(`/api/knowledge/categories/${categoryId}/knowledge`)
    if (!response.ok) {
      throw new Error('加载知识失败')
    }
    const data = await response.json()
    knowledges.value = data
  } catch (error) {
    console.error('加载知识失败:', error)
    ElMessage.error('加载知识失败')
  } finally {
    knowledgeLoading.value = false
  }
}

// 添加知识
const addKnowledge = (category: Category) => {
  currentCategory.value = category
  editingKnowledge.value = null
  knowledgeForm.value = { title: '', type: 'company_intro', content: '' }
  showAddKnowledge.value = true
}

// 编辑知识
const editKnowledge = (item: Knowledge) => {
  editingKnowledge.value = item
  knowledgeForm.value = {
    title: item.title,
    type: item.type,
    content: item.content,
  }
  showAddKnowledge.value = true
}

// 删除知识
const deleteKnowledge = async (item: Knowledge) => {
  try {
    await ElMessageBox.confirm(`确定要删除知识"${item.title}"吗？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })

    const response = await fetch(`/api/knowledge/knowledge/${item.id}`, {
      method: 'DELETE',
    })

    if (!response.ok) {
      throw new Error('删除失败')
    }

    ElMessage.success('删除成功')
    // 重新加载知识列表
    await loadKnowledge(currentCategory.value!.id)
    // 重新加载分类列表以更新计数
    await loadCategories()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 保存知识
const saveKnowledge = async () => {
  if (!knowledgeForm.value.title?.trim()) {
    ElMessage.warning('请输入知识标题')
    return
  }
  if (!knowledgeForm.value.content?.trim()) {
    ElMessage.warning('请输入知识内容')
    return
  }

  savingKnowledge.value = true
  try {
    if (editingKnowledge.value) {
      // 更新
      const response = await fetch(`/api/knowledge/knowledge/${editingKnowledge.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: knowledgeForm.value.title,
          type: knowledgeForm.value.type,
          content: knowledgeForm.value.content,
        }),
      })

      if (!response.ok) {
        throw new Error('更新失败')
      }

      ElMessage.success('更新成功')
    } else {
      // 新增
      const response = await fetch('/api/knowledge/knowledge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category_id: currentCategory.value!.id,
          title: knowledgeForm.value.title,
          type: knowledgeForm.value.type,
          content: knowledgeForm.value.content,
        }),
      })

      if (!response.ok) {
        throw new Error('创建失败')
      }

      ElMessage.success('添加成功')
    }

    showAddKnowledge.value = false
    resetKnowledgeForm()
    // 重新加载知识列表
    await loadKnowledge(currentCategory.value!.id)
    // 重新加载分类列表以更新计数
    await loadCategories()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    savingKnowledge.value = false
  }
}

// 重置知识表单
const resetKnowledgeForm = () => {
  editingKnowledge.value = null
  knowledgeForm.value = { title: '', type: 'company_intro', content: '' }
}

// 编辑分类
const editCategory = (category: Category) => {
  editingCategory.value = category
  categoryForm.value = {
    name: category.name,
    industry: category.industry || '',
    description: category.description || '',
    tagsInput: category.tags?.join(', ') || '',
    color: category.color,
  }
  showCreateCategory.value = true
}

// 删除分类
const deleteCategory = async (category: Category) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除企业分类"${category.name}"吗？删除后关联的知识也将被删除！`,
      '确认删除',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )

    const response = await fetch(`/api/knowledge/categories/${category.id}`, {
      method: 'DELETE',
    })

    if (!response.ok) {
      throw new Error('删除失败')
    }

    ElMessage.success('删除成功')
    // 重新加载分类列表
    await loadCategories()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 保存分类
const saveCategory = async () => {
  if (!categoryForm.value.name?.trim()) {
    ElMessage.warning('请输入企业名称')
    return
  }

  saving.value = true
  try {
    const tags = categoryForm.value.tagsInput
      ? categoryForm.value.tagsInput.split(',').map(t => t.trim()).filter(t => t)
      : []

    if (editingCategory.value) {
      // 更新
      const response = await fetch(`/api/knowledge/categories/${editingCategory.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: categoryForm.value.name,
          industry: categoryForm.value.industry,
          description: categoryForm.value.description,
          tags: tags.join(', '),
          color: categoryForm.value.color,
        }),
      })

      if (!response.ok) {
        throw new Error('更新失败')
      }

      ElMessage.success('更新成功')
    } else {
      // 新增
      const response = await fetch('/api/knowledge/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: categoryForm.value.name,
          industry: categoryForm.value.industry,
          description: categoryForm.value.description,
          tags: tags.join(', '),
          color: categoryForm.value.color,
        }),
      })

      if (!response.ok) {
        throw new Error('创建失败')
      }

      ElMessage.success('创建成功')
    }

    showCreateCategory.value = false
    resetCategoryForm()
    // 重新加载分类列表
    await loadCategories()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 重置分类表单
const resetCategoryForm = () => {
  editingCategory.value = null
  categoryForm.value = {
    name: '',
    industry: '',
    description: '',
    tagsInput: '',
    color: '#6366f1',
  }
}

// 格式化时间
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天更新'
  if (days === 1) return '昨天更新'
  if (days < 7) return `${days}天前更新`
  return date.toLocaleDateString('zh-CN')
}

// ==================== 生命周期 ====================
onMounted(() => {
  loadCategories()
  checkRAGFlowStatus()
})

// 检查RAGFlow连接状态
const checkRAGFlowStatus = async () => {
  try {
    // 尝试调用API检查RAGFlow状态
    const response = await fetch('/api/knowledge/categories')
    if (!response.ok) {
      console.warn('RAGFlow可能未连接')
    }
  } catch (error) {
    console.error('RAGFlow状态检查失败:', error)
  }
}
</script>

<style scoped lang="scss">
.knowledge-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
  padding: 24px;
  background: linear-gradient(135deg, #f8f9fc 0%, #f0f2f8 100%);
}

// 头部
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 28px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .header-icon {
      width: 52px;
      height: 52px;
      border-radius: 14px;
      background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;

      svg {
        width: 26px;
        height: 26px;
      }
    }

    .page-title {
      margin: 0 0 4px 0;
      font-size: 22px;
      font-weight: 600;
      color: #1a1f36;
    }

    .page-desc {
      margin: 0;
      font-size: 13px;
      color: #9ca3af;
    }
  }
}

// 企业分类区域
.categories-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  padding: 24px 28px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;

    .section-title {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #1a1f36;
    }
  }
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}

// 企业分类卡片
.category-card {
  background: #f9fafb;
  border-radius: 16px;
  padding: 20px;
  border: 2px solid transparent;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    border-color: #8b5cf6;
    box-shadow: 0 8px 24px rgba(139, 92, 246, 0.15);
    transform: translateY(-2px);
  }

  .card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 16px;

    .company-info {
      display: flex;
      align-items: center;
      gap: 14px;

      .company-avatar {
        width: 52px;
        height: 52px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 20px;
        color: white;
      }

      .company-details {
        .company-name {
          margin: 0 0 4px 0;
          font-size: 16px;
          font-weight: 600;
          color: #1a1f36;
        }

        .company-industry {
          font-size: 12px;
          color: #9ca3af;
        }
      }
    }

    .more-btn {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #9ca3af;
      transition: all 0.2s;

      &:hover {
        background: rgba(0, 0, 0, 0.04);
        color: #6b7280;
      }
    }
  }

  .card-body {
    flex: 1;

    .company-desc {
      font-size: 13px;
      color: #6b7280;
      margin: 0 0 16px 0;
      line-height: 1.6;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .knowledge-stats {
      display: flex;
      gap: 16px;
      margin-bottom: 14px;

      .stat-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: #6b7280;

        svg {
          color: #8b5cf6;
        }
      }
    }

    .card-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;

      .tag {
        padding: 4px 10px;
        background: rgba(139, 92, 246, 0.1);
        border-radius: 6px;
        font-size: 11px;
        color: #7c3aed;
      }
    }
  }

  .card-footer {
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: space-between;

    .update-time {
      font-size: 11px;
      color: #9ca3af;
    }

    .action-btn {
      padding: 6px 14px;
      background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
      border: none;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 500;
      color: white;
      cursor: pointer;
      transition: all 0.2s;

      &:hover {
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
      }
    }
  }
}

// 空状态
.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;

  .empty-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: rgba(139, 92, 246, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;

    svg {
      width: 36px;
      height: 36px;
      color: #8b5cf6;
    }
  }

  h3 {
    margin: 0 0 8px 0;
    font-size: 18px;
    font-weight: 500;
    color: #1a1f36;
  }

  p {
    margin: 0 0 24px 0;
    font-size: 14px;
    color: #9ca3af;
  }
}

// 知识抽屉
.drawer-content {
  display: flex;
  flex-direction: column;
  height: 100%;

  .drawer-header {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;

    .search-box {
      flex: 1;
    }
  }

  .knowledge-list {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 4px;
  }
}

.knowledge-item {
  background: #f9fafb;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;

  &:hover {
    border-color: #8b5cf6;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
  }

  .item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;

    .item-title {
      margin: 0;
      font-size: 15px;
      font-weight: 500;
      color: #1a1f36;
    }

    .item-more {
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #9ca3af;
      cursor: pointer;
      border-radius: 4px;

      &:hover {
        background: rgba(0, 0, 0, 0.04);
      }
    }
  }

  .item-content {
    margin: 0 0 12px 0;
    font-size: 13px;
    color: #6b7280;
    line-height: 1.6;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .item-meta {
    display: flex;
    align-items: center;
    gap: 12px;

    .item-type {
      padding: 3px 8px;
      background: rgba(139, 92, 246, 0.1);
      border-radius: 4px;
      font-size: 11px;
      color: #7c3aed;
    }

    .item-time {
      font-size: 11px;
      color: #9ca3af;
    }
  }
}

// 表单提示
.form-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #9ca3af;
}

// 颜色选择器
.color-picker {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;

  .color-option {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    cursor: pointer;
    border: 3px solid transparent;
    transition: all 0.2s;

    &:hover {
      transform: scale(1.1);
    }

    &.active {
      border-color: #1a1f36;
      box-shadow: 0 0 0 2px white, 0 0 0 4px #8b5cf6;
    }
  }
}

// 滚动条
.categories-grid::-webkit-scrollbar,
.knowledge-list::-webkit-scrollbar {
  width: 6px;
}

.categories-grid::-webkit-scrollbar-track,
.knowledge-list::-webkit-scrollbar-track {
  background: transparent;
}

.categories-grid::-webkit-scrollbar-thumb,
.knowledge-list::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;

  &:hover {
    background: #9ca3af;
  }
}

// 对话框样式
:deep(.category-dialog),
:deep(.knowledge-dialog) {
  .el-dialog {
    border-radius: 16px;
  }

  .el-dialog__header {
    padding: 20px 24px 10px;
    border-bottom: 1px solid #e5e7eb;

    .el-dialog__title {
      font-size: 16px;
      font-weight: 600;
      color: #1a1f36;
    }
  }

  .el-dialog__body {
    padding: 20px 24px;
  }

  .el-dialog__footer {
    padding: 16px 24px 20px;
    border-top: 1px solid #e5e7eb;
  }

  .el-form-item__label {
    font-weight: 500;
    color: #374151;
  }

  .el-input__wrapper,
  .el-textarea__inner {
    border-radius: 10px;

    &.is-focus {
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
    }
  }
}
</style>
