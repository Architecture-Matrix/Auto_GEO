# 智能建站功能文档

---

## 一、功能概述

智能建站是一个**可视化配置 + 实时预览 + 一键部署**的网站生成器，用户通过配置表单即可生成企业官网，支持 SFTP 和 S3/OSS 两种部署方式。

### 核心特性

| 特性 | 说明 |
|------|------|
| **双模板风格** | 商务旗舰版（深色）+ 现代生活版（浅色） |
| **实时预览** | 表单变化 800ms 防抖后自动刷新预览 |
| **拖拽式配置** | 数据指标、服务列表、案例列表等支持动态增删 |
| **一键部署** | 支持 SFTP 和 S3/OSS 部署到生产环境 |
| **自定义主题** | 支持自定义主色、强调色、图片等 |

---

## 二、技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              智能建站模块架构                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────┐         ┌──────────────────────────┐          │
│  │   前端配置向导            │         │      后端 API            │          │
│  │   ConfigWizard.vue       │◄────────┤   site_builder.py        │          │
│  │                          │  HTTP   │                          │          │
│  │  - 左侧：配置表单         │  JSON   │  - POST /sites/build     │          │
│  │  - 右侧：iframe 实时预览  │         │  - POST /sites/deploy    │          │
│  └──────────┬───────────────┘         └──────────┬───────────────┘          │
│             │                                     │                          │
│             │ 1. 监听表单变化 + 防抖               │                          │
│             │ 2. 调用 /sites/build                │                          │
│             │ 3. 更新 iframe src                  │                          │
│             │                                     │                          │
│             ▼                                     ▼                          │
│  ┌──────────────────────────┐         ┌──────────────────────────┐          │
│  │      静态预览             │         │    Jinja2 模板引擎        │          │
│  │   /static/sites/{id}/    │         │  site_generator.py       │          │
│  │       index.html         │◄────────│                          │          │
│  └──────────────────────────┘  渲染   │  - 模板目录: templates/   │          │
│                                     │  - 输出目录: static/sites/ │          │
│                                     └──────────┬───────────────┘          │
│                                                │                          │
│                                                ▼                          │
│                                     ┌──────────────────────────┐          │
│                                     │      HTML 模板            │          │
│                                     │  - corporate_v1.html      │          │
│                                     │  - cowboy_v1.html         │          │
│                                     └──────────────────────────┘          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                          部署服务 (可选)                                 ││
│  │  ┌─────────────────────┐         ┌─────────────────────┐                ││
│  │  │   SFTP 部署         │         │   S3/OSS 部署        │                ││
│  │  │   paramiko 库       │         │   boto3 库           │                ││
│  │  └─────────────────────┘         └─────────────────────┘                ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 关键目录结构

```
auto_geo_dev/
├── backend/
│   ├── api/
│   │   └── site_builder.py        # 建站 API 路由
│   ├── services/
│   │   ├── site_generator.py      # Jinja2 模板渲染服务
│   │   └── deploy_service.py      # SFTP/S3 部署服务
│   ├── templates/                 # Jinja2 模板目录
│   │   ├── corporate_v1.html      # 商务旗舰版模板
│   │   └── cowboy_v1.html         # 现代生活版模板
│   └── static/
│       └── sites/                 # 生成的站点文件
│           ├── {uuid}/
│           │   └── index.html
│           └── ...
│
└── fronted/
    └── src/
        └── views/
            └── site-builder/
                └── ConfigWizard.vue  # 建站配置向导页面
```

---

## 三、数据流详解

### 3.1 构建流程

```
用户修改表单 → watch 监听 → debounce(800ms) → POST /sites/build
                                                              │
                         ┌────────────────────────────────────┘
                         ▼
                   SiteGeneratorService
                         │
                         ├── 1. 获取模板 (corporate/cowboy)
                         ├── 2. 渲染数据到模板 (Jinja2)
                         ├── 3. 写入 static/sites/{site_id}/index.html
                         └── 4. 返回预览 URL
                         │
                         ▼
                   前端 iframe 加载预览
```

### 3.2 部署流程

```
用户点击部署 → 选择 SFTP/S3 → 填写配置 → POST /sites/deploy
                                                    │
                              ┌─────────────────────┘
                              ▼
                        DeployService
                              │
         ┌────────────────────┴────────────────────┐
         ▼                                         ▼
    SFTP 部署                                S3/OSS 部署
    (paramiko)                               (boto3)
         │                                         │
         ├── 连接服务器                            ├── 连接云存储
         ├── 递归上传文件                          ├── 上传文件
         └── 返回公网 URL                         └── 返回访问 URL
```

---

## 四、后端实现细节

### 4.1 API 接口

**文件**: `backend/api/site_builder.py`

#### 1. 构建站点接口

```python
@router.post("/sites/build")
def build_new_site(req: SiteBuildRequest):
    """构建站点 - 渲染 Jinja2 模板并生成静态 HTML"""
    site_id = uuid.uuid4().hex  # 生成唯一站点 ID
    result = generator.generate_site(
        site_id=site_id,
        data=req.config,          # 前端传入的配置数据
        template_id=req.template_id  # 模板 ID: corporate 或 cowboy
    )
    result['site_id'] = site_id
    return {"code": 200, "data": result}
```

#### 2. 部署站点接口

```python
@router.post("/sites/deploy")
def deploy_site(req: DeployRequest):
    """部署站点 - 支持 SFTP 和 S3/OSS"""
    deploy_svc = DeployService()

    if req.method == 'sftp':
        return deploy_svc.deploy_sftp(
            site_id=req.site_id,
            project_name=req.project_name,
            host=req.sftp_host,
            port=req.sftp_port,
            username=req.sftp_user,
            password=req.sftp_pass,
            remote_root=req.sftp_path,
            custom_domain=req.custom_domain
        )
    elif req.method == 's3':
        return deploy_svc.deploy_s3(
            site_id=req.site_id,
            project_name=req.project_name,
            endpoint=req.s3_endpoint,
            bucket=req.s3_bucket,
            access_key=req.s3_access_key,
            secret_key=req.s3_secret_key,
            custom_domain=req.custom_domain
        )
```

### 4.2 模板渲染服务

**文件**: `backend/services/site_generator.py`

```python
class SiteGeneratorService:
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), "../templates")
        output_dir = os.path.join(os.path.dirname(__file__), "../static/sites")
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.output_dir = output_dir

    def generate_site(self, site_id: str, data: dict, template_id: str = "corporate"):
        """生成站点 HTML"""
        # 模板映射
        template_map = {
            "corporate": "corporate_v1.html",
            "cowboy": "cowboy_v1.html"
        }
        template_file = template_map.get(template_id, "corporate_v1.html")
        template = self.env.get_template(template_file)

        # 渲染模板
        html_content = template.render(data)

        # 写入文件
        site_path = os.path.join(self.output_dir, site_id)
        os.makedirs(site_path, exist_ok=True)
        file_path = os.path.join(site_path, "index.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return {
            "local_path": file_path,
            "preview_url": f"/static/sites/{site_id}/index.html"
        }
```

### 4.3 部署服务

**文件**: `backend/services/deploy_service.py`

#### SFTP 部署实现

```python
def deploy_sftp(self, site_id, project_name, host, port, username, password, remote_root, custom_domain=None):
    """通过 SFTP 上传站点到远程服务器"""
    folder_name = self._sanitize_name(project_name)  # 安全化项目名
    target_remote_dir = f"{remote_root.rstrip('/')}/{folder_name}"

    local_path = os.path.join(STATIC_SITES_DIR, site_id)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=username, password=password)
    sftp = ssh.open_sftp()

    # 递归上传整个站点目录
    self._upload_dir(sftp, local_path, target_remote_dir)

    sftp.close()
    ssh.close()

    # 返回访问 URL
    if custom_domain:
        return f"https://{custom_domain}/{folder_name}/"
    else:
        return f"http://{host}/{folder_name}/"
```

---

## 五、前端实现细节

### 5.1 配置向导组件

**文件**: `fronted/src/views/site-builder/ConfigWizard.vue`

#### 核心表单数据结构

```typescript
const formData = reactive({
  // 基础配置
  template_id: "corporate",           // 模板选择: corporate / cowboy
  meta_title: "极速物流",
  company_name: "Turbo Logistics",

  // 主题颜色
  theme_color_primary: "#0f172a",     // 主色
  theme_color_accent: "#ef4444",      // 强调色

  // Hero 区块
  hero_badge_text: "Global Leader",
  company_slogan_hero: "连接全球<br>极速送达",
  image_hero_bg: "",                  // 背景图 URL

  // 数据指标（可动态增删）
  stats: [
    { label: "覆盖国家", value: "50+" },
    { label: "服务客户", value: "1000+" },
    { label: "准时交付率", value: "99%" },
  ],

  // 服务列表（可动态增删）
  services: [
    { title: "国际快递", desc: "全球范围快速配送", icon: "fa-plane" },
    { title: "仓储管理", desc: "智能仓储解决方案", icon: "fa-warehouse" },
  ],

  // 案例列表（可动态增删）
  cases: [
    { title: "某跨国企业", desc: "为其提供全球物流解决方案", image: "" },
  ],

  // 联系信息
  contact_address: "北京市朝阳区xxx",
  contact_phone: "400-xxx-xxxx",
  contact_email: "contact@example.com",

  // 其他图片
  image_about_team: "",
})
```

#### 实时预览逻辑

```typescript
import { watch } from 'vue'
import debounce from 'lodash.debounce'

// 防抖构建函数
const debouncedBuild = debounce(async () => {
  const response = await axios.post('http://localhost:8001/sites/build', {
    name: formData.company_name,
    config: formData,
    template_id: formData.template_id
  })
  previewUrl.value = `http://localhost:8001${response.data.data.preview_url}`
}, 800)  // 800ms 防抖

// 监听表单变化
watch(formData, () => {
  debouncedBuild()
}, { deep: true })
```

### 5.2 模板变量对照表

| 前端字段 | 模板变量 | 说明 |
|---------|---------|------|
| `meta_title` | `{{ meta_title }}` | 页面标题 |
| `company_name` | `{{ company_name }}` | 公司名称 |
| `theme_color_primary` | `{{ theme_color_primary }}` | 主色调 |
| `theme_color_accent` | `{{ theme_color_accent }}` | 强调色 |
| `hero_badge_text` | `{{ hero_badge_text }}` | Hero 区徽章文字 |
| `company_slogan_hero` | `{{ company_slogan_hero }}` | Slogan |
| `image_hero_bg` | `{{ image_hero_bg }}` | Hero 背景图 |
| `stats` | `{% for stat in stats %}` | 数据指标列表 |
| `services` | `{% for svc in services %}` | 服务列表 |
| `cases` | `{% for case in cases %}` | 案例列表 |
| `contact_address` | `{{ contact_address }}` | 联系地址 |
| `contact_phone` | `{{ contact_phone }}` | 联系电话 |
| `contact_email` | `{{ contact_email }}` | 联系邮箱 |

---

## 六、模板系统

### 6.1 商务旗舰版模板

**文件**: `backend/templates/corporate_v1.html` (309 行)

- **风格**: 深色商务风，主色调 `#0f172a`
- **技术栈**: TailwindCSS CDN + Font Awesome 图标
- **区块**:
  1. 导航栏（固定顶部）
  2. Hero 首屏（大背景图 + Slogan）
  3. Stats 数据展示（3列布局）
  4. Services 服务列表（3列网格）
  5. About 关于我们（图文混排）
  6. Qualifications 资质展示
  7. Cases 案例展示（2x2网格）
  8. Contact 联系方式（底部）

### 6.2 现代生活版模板

**文件**: `backend/templates/cowboy_v1.html` (381 行)

- **风格**: 浅色极简风，背景色 `#fdfbf7`
- **技术栈**: TailwindCSS + Font Awesome + Manrope 字体 + Swiper 轮播
- **特色功能**:
  - **跑马灯效果**: Stats 使用 Swiper 无缝滚动
  - **磁性按钮动画**: 鼠标悬停时按钮跟随效果
  - **滚动显现动画**: 元素进入视口时淡入
  - **自适应案例布局**:
    - 1个案例: 单列大图
    - 2个案例: 2列布局
    - 3+个案例: 3列网格

### 6.3 模板变量示例

```jinja2
<!-- 条件渲染 -->
{% if services %}
<section class="services">
  {% for svc in services %}
  <div class="service-card">
    <i class="{{ svc.icon }}"></i>
    <h3>{{ svc.title }}</h3>
    <p>{{ svc.desc }}</p>
  </div>
  {% endfor %}
</section>
{% endif %}

<!-- 样式变量 -->
<style>
  :root {
    --primary: {{ theme_color_primary }};
    --accent: {{ theme_color_accent }};
  }
</style>
```

---

## 七、部署配置说明

### 7.1 SFTP 部署

适用于有自己的 Linux 服务器的用户。

**所需参数**:
| 参数 | 说明 | 示例 |
|------|------|------|
| `sftp_host` | SFTP 服务器地址 | `192.168.1.100` |
| `sftp_port` | SFTP 端口 | `22` |
| `sftp_user` | 用户名 | `root` |
| `sftp_pass` | 密码 | `******` |
| `sftp_path` | 远程根目录 | `/var/www/html` |
| `custom_domain` | 自定义域名（可选） | `www.example.com` |

**上传逻辑**:
- 项目名会被安全化处理（只保留字母、数字、横杠）
- 上传到 `{remote_root}/{安全化项目名}/` 目录
- 返回访问 URL: `http://{host}/{安全化项目名}/`

### 7.2 S3/OSS 部署

适用于使用云对象存储的用户。

**所需参数**:
| 参数 | 说明 | 示例 |
|------|------|------|
| `s3_endpoint` | S3 兼容 API 端点 | `https://s3.amazonaws.com` |
| `s3_bucket` | 存储桶名称 | `my-websites` |
| `s3_access_key` | Access Key ID | `AKIAIOSFODNN7EXAMPLE` |
| `s3_secret_key` | Secret Access Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `custom_domain` | 自定义域名（可选） | `cdn.example.com` |

**支持的云服务商**:
- AWS S3
- 阿里云 OSS
- 腾讯云 COS
- MinIO（自建）

---

## 八、依赖项

**文件**: `backend/requirements.txt`

```
# Jinja2 是 FastAPI 内置依赖，无需单独安装
paramiko==3.4.0    # SFTP 部署
boto3==1.34.19     # S3/OSS 部署
```

---

## 九、路由注册

**前端路由**: `fronted/src/router/index.ts`

```typescript
{
  path: 'site-builder',
  name: 'SiteBuilder',
  component: () => import('@/views/site-builder/ConfigWizard.vue'),
  meta: { title: '智能建站', icon: 'Platform', order: 3 },
}
```

**后端路由**: `backend/main.py`

```python
from backend.api import site_builder

app.include_router(site_builder.router)  # 注册建站路由
```

**静态资源挂载**: `backend/main.py`

```python
# 创建 sites 目录
if not os.path.exists(os.path.join(static_dir, "sites")):
    os.makedirs(os.path.join(static_dir, "sites"))

# 挂载静态资源
app.mount("/static", StaticFiles(directory=static_dir), name="static")
```

---

## 十、注意事项

### 10.1 架构特点

1. **无数据库持久化**: 站点配置数据仅存在于前端状态，刷新页面会丢失。如需保存，需要扩展存储逻辑。

2. **每次构建生成新 UUID**: 每次点击预览都会生成新的站点目录，不会覆盖已有文件。`static/sites/` 目录会逐渐增大，建议定期清理。

3. **不经过 n8n**: 建站模块是独立的前后端直连架构，不使用 n8n 工作流。

### 10.2 安全建议

1. **SFTP 凭证**: 生产环境不应明文传输密码，建议使用密钥认证或环境变量。

2. **项目名安全化**: 部署时对项目名做了安全处理，防止路径遍历攻击。

3. **限制上传**: 建议限制单个站点的大小和数量。

### 10.3 扩展方向

| 功能 | 状态 | 说明 |
|------|------|------|
| 多页面支持 | 未实现 | 目前只支持单页 |
| 数据库持久化 | 未实现 | 配置保存到数据库 |
| 站点历史记录 | 未实现 | 查看历史版本 |
| 模板市场 | 未实现 | 用户自定义模板 |
| 在线编辑器 | 未实现 | 可视化拖拽编辑 |

---

## 十一、完整文件清单

| 层级 | 文件路径 | 行数 | 作用 |
|------|---------|------|------|
| API 路由 | `backend/api/site_builder.py` | 75 | `/sites/build` 和 `/sites/deploy` 接口 |
| 服务层 | `backend/services/site_generator.py` | 55 | Jinja2 模板渲染引擎 |
| 服务层 | `backend/services/deploy_service.py` | 95 | SFTP/S3 部署服务 |
| 模板 | `backend/templates/corporate_v1.html` | 309 | 商务旗舰版模板 |
| 模板 | `backend/templates/cowboy_v1.html` | 381 | 现代生活版模板 |
| 前端页面 | `fronted/src/views/site-builder/ConfigWizard.vue` | 370 | 建站配置向导 |
| 应用入口 | `backend/main.py` | - | 路由注册 + 静态资源挂载 |
| 前端路由 | `fronted/src/router/index.ts` | - | 路由注册 |

---

**文档创建时间：** 2025-02-10
**版本：** v1.0
