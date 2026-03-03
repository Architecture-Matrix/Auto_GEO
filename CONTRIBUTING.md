# 贡献指南

> 欢迎加入AutoGeo项目！这里有一份指南，让你快速上手贡献代码！

## 🎯 我们需要什么样的贡献

```
✅ Bug修复（找问题修问题的都是好汉）
✅ 新功能（有好点子尽管提）
✅ 文档改进（发现文档错误直接修）
✅ 性能优化（让系统跑得更快的都是大神）
✅ 代码重构（让代码更优雅的艺术家）
✅ 测试用例（写测试的都是负责任的好人）
✅ 问题反馈（用得爽不爽都要告诉我们）
```

---

## 🚀 快速开始

### 第一次贡献？

如果你是第一次参与开源项目，别担心，一步步来！

### 1. 准备工作

```bash
# 1. Fork这个项目到你的GitHub账号
# 点击页面右上角的Fork按钮

# 2. 克隆你Fork的项目
git clone https://github.com/你的用户名/auto_geo.git

# 3. 进入项目目录
cd auto_geo

# 4. 添加上游仓库（方便后续同步）
git remote add upstream https://github.com/Architecture-Matrix/auto_geo.git

# 5. 查看远程仓库配置
git remote -v
# 应该看到:
# origin    https://github.com/你的用户名/auto_geo.git (fetch)
# origin    https://github.com/你的用户名/auto_geo.git (push)
# upstream  https://github.com/Architecture-Matrix/auto_geo.git (fetch)
# upstream  https://github.com/Architecture-Matrix/auto_geo.git (push)
```

### 2. 配置开发环境

```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt
playwright install chromium

# 安装前端依赖
cd ../fronted
npm install

# 启动n8n（参考README.md）
```

### 3. 创建你的第一个分支

```bash
# 确保你在main分支
git checkout main

# 从上游仓库同步最新代码
git pull upstream main

# 创建你的功能分支（命名规范见下文）
git checkout -b feature/your-feature-name
```

---

## 🌿 分支命名规范

```bash
# 功能开发
feature/功能名称-简短描述
例: feature/geo-dashboard-monitor

# Bug修复
fix/问题描述-简短描述
例: fix/login-cookie-expire

# 紧急修复
hotfix/紧急问题描述
例: hotfix/production-crash

# 重构
refactor/模块名称-重构内容
例: refactor/api-service-cleanup

# 文档
docs/文档类型-内容
例: docs/api-guide-update

# 测试
test/测试模块-内容
例: test/backend-api-coverage
```

---

## ✍️ 提交规范

### Commit Message格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加关键词蒸馏API` |
| `fix` | Bug修复 | `fix: 修复登录cookie过期` |
| `docs` | 文档更新 | `docs: 更新API文档` |
| `style` | 代码格式 | `style: 统一缩进格式` |
| `refactor` | 重构 | `refactor: 重构服务层` |
| `perf` | 性能优化 | `perf: 优化数据库查询` |
| `test` | 测试相关 | `test: 添加单元测试` |
| `chore` | 构建/工具 | `chore: 更新依赖版本` |

### 提交示例

```bash
# 简单提交
git commit -m "feat: 添加收录检测API端点"

# 带说明的提交
git commit -m "fix: 修复知乎发布失败问题

- 修复cookie验证逻辑
- 添加错误重试机制
- 更新日志输出

Closes #123"
```

### 提交频率

- ✅ 频繁小提交，一个功能点就提交一次
- ✅ 每次提交保证代码能运行
- ❌ 别提交半成品代码
- ❌ 别一次提交一堆改动的代码

---

## 🔀 提交PR流程

### PR前检查清单

```markdown
## 代码自检
- [ ] 本地测试通过
- [ ] 代码规范检查通过（ESLint/Pylint）
- [ ] 添加必要的注释
- [ ] 更新相关文档

## 功能测试
- [ ] 新功能测试通过
- [ ] 回归测试通过（确保没改坏旧功能）
- [ ] 边界情况测试

## PR描述
- [ ] 填写PR描述模板
- [ ] 关联相关Issue
- [ ] 添加截图（如有UI变更）
```

### 创建PR步骤

```bash
# 1. 推送你的分支到GitHub
git push origin feature/your-feature-name

# 2. 在GitHub上创建Pull Request
# - 访问 https://github.com/你的用户名/auto_geo
# - 点击 "Pull requests" -> "New pull request"
# - 选择你的分支
# - 填写PR描述（使用PR模板）

# 3. 等待代码审查
# - 审查者会提出意见
# - 根据意见修改代码
# - 响应审查评论

# 4. 合并后删除你的分支
git checkout main
git pull upstream main
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

---

## 📝 代码规范

### Python代码规范

```python
# 遵循PEP 8规范
# 使用有意义的变量名（别tm用a,b,c这种SB命名）
# 添加函数文档字符串

def get_user_keywords(user_id: int) -> list[dict]:
    """
    获取用户的关键词列表

    Args:
        user_id: 用户ID

    Returns:
        关键词列表，格式: [{"id": 1, "keyword": "xxx"}, ...]
    """
    pass
```

### JavaScript/TypeScript代码规范

```javascript
// 使用ES6+语法
// 添加JSDoc注释
// 使用有意义的变量名

/**
 * 获取用户关键词列表
 * @param {number} userId - 用户ID
 * @returns {Promise<Array>} 关键词列表
 */
async function getUserKeywords(userId) {
  // ...
}
```

### 注释规范

```python
# ✅ 好的注释（解释为什么）
# 使用缓存避免频繁查询数据库
cached_data = cache.get(key)

# ❌ 坏的注释（重复代码内容）
# 获取缓存
cached_data = cache.get(key)
```

---

## 🧪 测试规范

### 单元测试

```python
# 测试文件命名: test_模块名.py
# 放在tests/目录下

def test_get_keywords():
    """测试获取关键词功能"""
    # Arrange
    user_id = 1

    # Act
    result = get_user_keywords(user_id)

    # Assert
    assert len(result) > 0
    assert result[0]['id'] == 1
```

### 测试覆盖率

```bash
# 运行测试
pytest tests/

# 查看覆盖率
pytest --cov=backend tests/
```

---

## 📚 文档贡献

### 什么样的文档需要贡献？

```
✅ 发现文档错误直接修正
✅ 补充缺失的使用说明
✅ 添加代码示例
✅ 翻译文档
✅ 完善API文档
✅ 更新过时的配置说明
```

### 文档格式

```markdown
# 一级标题

## 二级标题

### 三级标题

**加粗文本**
*斜体文本*

`行内代码`

```python
代码块
```

- 列表项1
- 列表项2

> 引用文本

[链接文字](链接地址)
```

---

## 🐛 报告Bug

### 报告Bug前

1. 先搜索Issue，确认问题未被报告
2. 确认是代码问题还是环境配置问题
3. 准备好复现步骤和环境信息

### 报告Bug时

1. 使用Bug报告模板
2. 详细描述复现步骤
3. 附上错误日志和截图
4. 提供环境信息（系统版本、软件版本等）

---

## ✨ 提出新功能

### 提功能前

1. 先看项目Roadmap（如果有）
2. 在Issue里讨论，确认需求合理
3. 等项目Owner确认后再开发

### 提功能时

1. 使用功能请求模板
2. 说明使用场景和价值
3. 提供实现思路（如果有）
4. 标注优先级

---

## 🔄 保持同步

```bash
# 定期从上游仓库同步代码
git checkout main
git pull upstream main
git push origin main

# 将上游更新合并到你的分支
git checkout feature/your-feature
git merge main
```

---

## 💬 沟通渠道

```
日常讨论: GitHub Issue
代码审查: PR评论
紧急问题: @项目Owner
```

---

## ⚠️ 注意事项

### 不能做的事

```markdown
❌ 未经讨论直接修改核心架构
❌ 提交无法运行的代码
❌ 不写测试就提交PR
❌ PR描述空白
❌ 审查意见不回应就强行合并
❌ 提交大文件（>5MB）
❌ 提交敏感信息（密码、密钥等）
```

### 必须做的事

```markdown
✅ 提交前自测
✅ 遵循代码规范
✅ 写清晰的commit message
✅ 填写完整的PR描述
✅ 响应审查意见
✅ 更新相关文档
✅ 保持代码简洁（KISS原则）
✅ 避免重复代码（DRY原则）
```

---

## 🏆 贡献者名单

感谢所有贡献者！你的名字会出现在[贡献者列表](https://github.com/Architecture-Matrix/auto_geo/graphs/contributors)中。

---

## 📖 推荐阅读

- [团队协作规范](./docs/TEAM_COLLABORATION_GUIDE.md)
- [项目README](./README.md)
- [Git工作流](https://www.atlassian.com/git/tutorials/comparing-workflows)

---

## ❓ 常见问题

### Q: 我新手，代码写得烂怎么办？

**A**: 艹，别担心！咱小团队看重态度，代码有问题大家一起review，慢慢就进步了！

### Q: 提交PR后多久会有人review？

**A**: 一般工作日24小时内会响应，如果超过24小时没人理，直接@小a催一下！

### Q: 我的PR被拒绝了怎么办？

**A**: 别灰心！看看审查意见，修改后再提。代码review是学习的好机会！

### Q: 我不懂代码也能贡献吗？

**A**: 当然！可以提Bug、提建议、改进文档、分享使用经验，这些都是有价值的贡献！

---

**最后更新**: 2026-02-03
**维护者**: 小a

---

> 艹，别看文档挺多，其实就几点：
> 1. 先Fork项目
> 2. 按规范写代码和提交
> 3. PR描述写清楚
> 4. 虚心接受review意见
> 5. 完事了清理分支
>
> 好了，开搞吧！💪
