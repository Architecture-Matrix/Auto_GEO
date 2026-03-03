# AutoGeo 团队 PR 协作流程

**更新时间**: 2026-02-26

---

## 📋 流程概览

```
创建分支 → 修改代码 → Push推送 → 创建PR → CI审查 → 修改完善 → 合并
  (1)      (2)       (3)       (4)       (5)       (6)       (7)
```

**7步完整流程**，每一步都很关键，跳过任何一步都可能导致SB问题！

---

## 第一步：创建新分支

### 分支命名规范

| 前缀 | 用途 | 示例 |
|-----|------|------|
| `feat/` | 新功能 | `feat/user-login` |
| `fix/` | Bug修复 | `fix/database-connection` |
| `hotfix/` | 紧急生产修复 | `hotfix/security-leak` |
| `refactor/` | 代码重构 | `refactor/optimize-query` |
| `docs/` | 文档更新 | `docs/api-readme` |
| `test/` | 测试相关 | `test/add-unit-tests` |
| `style/` | 代码格式调整 | `style/ruff-format` |
| `perf/` | 性能优化 | `perf/cache-optimization` |
| `ci/` | CI/CD相关 | `ci/add-workflow` |
| `chore/` | 杂项 | `chore/update-deps` |

### 创建分支命令

```bash
# 1. 确保本地是最新的
git checkout main
git pull origin main

# 2. 创建并切换到新分支
git checkout -b feat/your-feature-name

# 或者使用简写
git switch -c feat/your-feature-name
```

### 分支命名规范

**✅ 好的分支名**:
- `feat/oauth-login` - 清楚表明是OAuth登录功能
- `fix/database-timeout` - 明确是数据库超时问题修复
- `refactor/user-service` - 重构用户服务

**❌ SB分支名**:
- `new-branch` - 没人知道你要干啥
- `fixbug` - 修复了什么bug？
- `test` - 测试什么？
- `update` - 更新了什么？

**备注**:
- 用英文，别tm用中文（兼容性问题）
- 用短横线 `-` 分隔，别用下划线 `_`
- 名字要一眼能看懂是干什么的
- 如果是Issue相关，可以加Issue编号：`fix/123-database-error`

---

## 第二步：修改代码

### 开发前检查清单

- [ ] 确认需求或Bug描述清楚
- [ ] 本地环境能正常启动
- [ ] 知道要修改哪些文件
- [ ] 了解现有的代码规范

### 代码规范

**Backend (Python)**:
```bash
cd backend
# 代码检查
ruff check .
# 格式化
ruff format .
# 类型检查
mypy api/
```

**Frontend (TypeScript/React)**:
```bash
cd frontend
# 代码检查
npm run lint
# 类型检查
npm run type-check
# 格式化
npm run format
```

### 提交代码规范

```bash
# 查看修改状态
git status

# 添加修改的文件
git add backend/xxx.py
# 或者添加所有修改
git add .

# 提交（遵循 Conventional Commits 规范）
git commit -m "feat: 添加用户登录功能"

# 或者添加详细描述
git commit -m "feat: 添加用户登录功能

- 实现OAuth2.0认证
- 添加登录API端点
- 更新相关文档"
```

**提交格式规范**:
```
<类型>: <简短描述>

[可选的详细描述]

[可选的关联Issue]
```

| 类型 | 说明 | 示例 |
|-----|------|------|
| `feat` | 新功能 | `feat: 添加用户注册功能` |
| `fix` | Bug修复 | `fix: 修复数据库连接超时` |
| `docs` | 文档更新 | `docs: 更新API文档` |
| `style` | 格式调整 | `style: 使用ruff格式化代码` |
| `refactor` | 重构 | `refactor: 优化数据库查询` |
| `test` | 测试 | `test: 添加单元测试` |
| `chore` | 杂项 | `chore: 更新依赖版本` |
| `perf` | 性能优化 | `perf: 添加缓存层` |
| `ci` | CI/CD | `ci: 添加自动化部署` |

---

## 第三步：Push到远程分支

### 推送命令

```bash
# 推送到远程
git push -u origin feat/your-feature-name

# -u 参数设置上游分支，以后直接 git push 即可
```

### 推送后检查

推送成功后，GitHub会自动显示创建PR的提示：
```
✓ Your branch is up to date with 'origin/feat/your-feature-name'.

hint: Create a pull request for 'feat/your-feature-name' on GitHub:
      https://github.com/Architecture-Matrix/Auto_GEO/pull/new/feat/your-feature-name
```

### 如果推送失败

**情况1: 远程有新提交**
```bash
# 先rebase远程的最新代码
git pull --rebase origin main
# 解决冲突后
git push
```

**情况2: 权限问题**
- 检查是否有仓库写入权限
- 检查SSH密钥是否配置正确

---

## 第四步：创建 Pull Request

### 通过网页创建PR

1. 访问 GitHub 仓库页面
2. 点击 **"Pull requests"** → **"New pull request"**
3. 选择你的分支：`feat/your-feature-name`
4. 点击 **"Create pull request"**

### PR 模板

GitHub会自动加载PR模板（`.github/PULL_REQUEST_TEMPLATE.md`），填写以下内容：

```markdown
## 📝 变更说明
<!-- 简短描述这个PR做了什么 -->
添加了XXX功能，修复了XXX问题

## 🔗 关联Issue
<!-- 关联的Issue编号（如果有的话） -->
Closes #123

## 📋 变更类型
<!-- 选择适用的类型 -->
- [ ] feat: 新功能
- [ ] fix: Bug修复
- [ ] docs: 文档更新
- [ ] style: 代码格式
- [ ] refactor: 重构
- [ ] test: 测试
- [ ] chore: 杂项

## ✅ 检查清单
<!-- 提交前确认 -->
- [ ] 代码遵循项目规范
- [ ] 已添加必要的测试
- [ ] 已更新相关文档
- [ ] 本地测试通过
- [ ] 无合并冲突

## 📸 截图/演示
<!-- 如果是UI变更，请添加截图 -->

## 🧪 测试说明
<!-- 如何测试这些变更 -->
1. 启动后端
2. 访问 XXX 端点
3. 验证 XXX 功能

## 💬 其他说明
<!-- 任何需要评审人注意的信息 -->
```

### PR 标题规范

与commit message保持一致：
```
feat: 添加用户登录功能
fix: 修复数据库连接超时
docs: 更新API文档
```

### 指定评审人

在PR右侧边栏：
- **Reviewers**: 选择需要评审的人员
- **Assignees**: 指定负责人
- **Labels**: 添加标签（如 `enhancement`, `bug`, `documentation`）

---

## 第五步：自动审查

### CI 自动检查流程

创建PR后，以下CI会自动运行：

#### 1. Startup Validation（启动验证）
- **运行时间**: ~2分钟
- **检查内容**:
  - 后端能否正常启动
  - 前端能否正常构建
  - 依赖文件是否完整
  - 文档是否齐全

#### 2. Backend CI / Frontend CI（代码检查）
- **运行时间**: ~2-5分钟
- **检查内容**:
  - 代码规范检查 (Ruff/ESLint)
  - 类型检查 (MyPy/TypeScript)
  - 单元测试
  - 代码覆盖率

#### 3. Dependency Review（依赖审查）
- **运行时间**: ~1分钟
- **检查内容**:
  - 新增依赖的安全漏洞
  - 许可证问题

#### 4. GitHub Copilot（代码审查）
- 自动生成代码审查意见
- 检测潜在bug和改进建议

### 查看审查结果

在PR页面底部，可以看到所有检查的状态：
- ✅ **绿色对勾** - 通过
- ❌ **红色叉号** - 失败（必须修复）
- ⚠️ **黄色圆圈** - 警告（建议修复）

---

## 第六步：修改完善

### 如果CI检查失败

#### 1. 查看失败原因

点击失败的检查项，查看详细日志：

```
Backend CI / lint (xxxxx)  Failed

View details → 查看完整日志
```

#### 2. 本地复现并修复

```bash
# 拉取最新的main分支代码
git checkout main
git pull origin main

# 切换回你的分支
git checkout feat/your-feature-name

# 合并最新的main代码
git merge main

# 本地运行检查
cd backend
ruff check .
ruff format .
mypy api/

# 修复问题
```

#### 3. 提交修复

```bash
git add .
git commit -m "fix: 修复CI检查失败的问题"
git push
```

### 如果评审人提出意见

#### 1. 查看评审意见

在PR的 **"Files changed"** 标签页，可以看到评审人的具体评论：
- 💬 **普通评论** - 讨论和建议
- ✅ **批准** - 评审通过
- 🔄 **请求修改** - 需要修改后再次评审

#### 2. 回复并修改

```bash
# 修改代码
# ... 编辑文件 ...

# 提交修改
git add .
git commit -m "fix: 根据评审意见修改XXX"
git push
```

#### 3. 回复评审意见

在PR中回复评审人的评论：
- 如果已修复：回复 "已修复，请重新审查"
- 如果有疑问：提出问题，讨论解决方案
- 如果不建议：说明理由，寻求共识

### 常见CI失败及修复

| 失败类型 | 原因 | 修复方法 |
|---------|------|---------|
| **Ruff检查失败** | 代码格式不规范 | `ruff format .` |
| **类型检查失败** | 类型注解错误 | 修复类型问题 |
| **单元测试失败** | 测试用例不通过 | 修复代码或测试 |
| **Gitleaks失败** | 密钥泄露 | 移除硬编码密钥 |
| **Trivy失败** | 依赖漏洞 | 更新依赖版本 |

---

## 第七步：合并

### 合并前的最终检查

- [ ] ✅ 所有CI检查通过
- [ ] ✅ 至少一名评审人批准
- [ ] ✅ 代码合并冲突已解决
- [ ] ✅ 功能测试通过
- [ ] ✅ 文档已更新

### 合并方式

GitHub提供三种合并方式：

| 方式 | 说明 | 优点 | 缺点 |
|-----|------|------|------|
| **Squash merge** | 压缩为单个提交 | ✅ 历史整洁<br>✅ 每个功能一个commit | - 丢失分支历史 |
| **Merge commit** | 创建合并提交 | ✅ 保留完整历史 | ❌ 历史杂乱 |
| **Rebase merge** | 变基合并 | ✅ 线性历史 | ❌ 容易搞乱历史 |

**重要：团队统一使用 Squash merge**

为了保持Git历史整洁，**所有PR合并时统一使用 Squash merge**：

- ✅ 每个功能在main分支只有一个commit
- ✅ 历史清晰，容易回溯
- ✅ 避免无意义的"Merge branch xxx"提交

**Commit信息规范**：
合并时会自动生成commit信息，请确保：
- 标题遵循 Conventional Commits（`feat:` / `fix:` 等）
- 描述清晰说明变更内容

### 合并操作

1. 点击 **"Merge pull request"** 下拉箭头
2. 选择 **"Squash and merge"**
3. 确认commit信息正确
4. 点击 **"Confirm squash and merge"**

### 合并后

合并成功后：
1. ✅ PR会自动关闭
2. ✅ 关联的Issue会自动关闭（如果PR描述中包含 `Closes #xxx`）
3. ✅ 触发生产部署（如果是合并到main分支）

### 清理分支

```bash
# 删除本地分支
git branch -d feat/your-feature-name

# 删除远程分支
git push origin --delete feat/your-feature-name

# 或者使用简写
git push origin :feat/your-feature-name
```

---

## 🚨 常见问题

### Q1: PR有冲突怎么办？

**A**: 本地解决冲突后再推送

```bash
# 1. 切换到main，拉取最新代码
git checkout main
git pull origin main

# 2. 切换回你的分支
git checkout feat/your-feature-name

# 3. Rebase main
git rebase main

# 4. 解决冲突
# 编辑冲突文件，移除 <<<<<<< ======= >>>>>>> 标记

# 5. 标记冲突已解决
git add <冲突文件>

# 6. 继续rebase
git rebase --continue

# 7. 强制推送（因为是rebase）
git push --force-with-lease
```

### Q2: CI一直运行中怎么办？

**A**: 等待或取消重试

```bash
# 如果超过30分钟还在运行，可能是卡住了
# 在GitHub PR页面点击 "Cancel workflow"
# 然后重新推送一个空commit触发CI

git commit --allow-empty -m "ci: 触发CI重试"
git push
```

### Q3: 怎样快速检查本地代码是否通过CI？

**A**: 本地运行相同的检查命令

```bash
# Backend
cd backend
ruff check .
ruff format --check .
mypy api/
pytest tests/

# Frontend
cd frontend
npm run lint
npm run type-check
npm run test
```

### Q4: PR还没有合并就要开始新任务怎么办？

**A**: 可以创建多个分支，并行开发

```bash
# 当前分支还在等待合并
git checkout main
git pull origin main

# 创建新的功能分支
git checkout -b feat/another-feature
```

### Q5: 评审人一直不审核怎么办？

**A**: 可以在PR中 @ 相关人员

在PR评论中：
```
@评审人名 请帮忙审查一下这个PR，谢谢！
```

或者在团队群里发消息提醒。

---

## 📊 PR协作流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                         开始                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  第一步：创建新分支                                              │
│  git checkout -b feat/your-feature-name                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  第二步：修改代码                                                │
│  - 编写功能代码                                                  │
│  - 遵循代码规范                                                  │
│  - 本地测试通过                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  第三步：提交并推送                                              │
│  git add . && git commit -m "feat: xxx"                         │
│  git push -u origin feat/your-feature-name                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  第四步：创建PR                                                  │
│  - 填写PR模板                                                    │
│  - 关联Issue                                                     │
│  - 指定评审人                                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  第五步：自动审查                                                │
│  - Startup Validation ✅                                         │
│  - Backend/Frontend CI ✅                                       │
│  - Dependency Review ✅                                         │
│  - GitHub Copilot ✅                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                  通过                  失败
                    │                   │
                    ▼                   ▼
        ┌─────────────────────┐   ┌─────────────┐
        │  第六步：修改完善    │   │  修复问题    │
        │  - 处理评审意见      │   │  - 查看日志  │
        │  - 优化代码          │   │  - 本地修复  │
        │  - 更新文档          │   │  - 重新推送  │
        └─────────────────────┘   └─────────────┘
                    │                   │
                    └─────────┬─────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  第七步：合并                                                    │
│  - 所有检查通过                                                  │
│  - 评审人批准                                                    │
│  - 合并到main                                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  合并后操作                                                      │
│  - 删除本地分支                                                  │
│  - 删除远程分支                                                  │
│  - 通知团队                                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 总结

**PR协作黄金法则**:

1. **分支命名要清晰** - 一眼看出是干什么的
2. **提交信息要规范** - 遵循 Conventional Commits
3. **PR描述要完整** - 关联Issue、说明变更、提供测试方法
4. **CI不过不合并** - 红灯就是红灯，所有检查必须通过
5. **评审意见要重视** - 别人花时间review，认真对待
6. **冲突要及时解决** - 别拖着，越拖越难搞
7. **合并用Squash** - 保持Git历史整洁，每个功能一个commit
8. **合并后要清理** - 别留一堆无用分支

**团队协作的核心**:
- ✅ **代码质量** - CI自动检查，人肉Review辅助
- ✅ **沟通透明** - PR描述清楚，及时响应评论
- ✅ **尊重他人** - 评审意见认真对待，别当成找茬
- ✅ **持续改进** - 每次PR都是学习机会
- ✅ **历史整洁** - 统一使用Squash merge，保持main分支干净

---

**最后更新**: 2026-02-26
