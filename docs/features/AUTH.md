# AutoGeo 账号授权功能文档

**文档版本**：v1.0
**更新时间**：2026-01-09
**维护人员**：开发者

---

## 一、功能概述

账号授权功能允许用户通过浏览器手动登录各平台（知乎、百家号、搜狐、头条），系统自动提取登录cookie并加密保存到数据库。

### 核心特性

| 特性 | 说明 |
|-----|------|
| **双标签页设计** | 目标平台登录页 + 本地控制页 |
| **CORS绕过** | 使用 `expose_function` 直接暴露Python函数给浏览器 |
| **全量Cookie保存** | 保存全部cookies（按调研文档建议，不精简） |
| **严格登录验证** | 只检查最核心的关键cookie是否存在 |
| **自动关闭浏览器** | 授权成功后自动关闭浏览器 |
| **加密存储** | AES-256加密保存cookies和storage_state |

---

## 二、技术架构

### 2.1 核心文件

| 文件 | 说明 |
|-----|------|
| `services/playwright_mgr.py` | Playwright管理器，核心授权逻辑 |
| `static/auth_confirm.html` | 本地控制页UI |
| `api/account.py` | 授权API接口 |
| `test_auth.py` | 手动测试脚本 |
| `test_auth_unit.py` | 单元测试 |

### 2.2 授权流程图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   前端调用API    │────▶│  创建授权任务    │────▶│  打开两个标签页  │
│ /auth/start     │     │ playwright_mgr  │     │ 目标页+控制页    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  用户在目标页    │
              │  完成平台登录    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  切换到控制页    │
              │  点击"完成授权"  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ 调用confirmAuth  │
              │ (expose_function)│
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  提取所有cookies │
              │  过滤关键cookies │
              │  验证登录状态    │
              └────────┬────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼                       ▼
    ┌──────────────┐      ┌──────────────┐
    │  验证成功     │      │  验证失败     │
    │  保存到数据库 │      │  返回错误信息 │
    │  关闭浏览器   │      └──────────────┘
    └──────────────┘
```

---

## 三、关键代码说明

### 3.1 CORS绕过方案

使用 `context.expose_function()` 将Python函数直接暴露给浏览器，绕过file://协议的CORS限制：

```python
# services/playwright_mgr.py:327
await context.expose_function("confirmAuth", confirm_auth_wrapper)
```

浏览器JavaScript直接调用：
```javascript
// auth_confirm.html
const result = await window.confirmAuth(taskId);
```

### 3.2 Cookie保存策略（按调研文档建议）

**保存全部cookies，不精简！** 原因是各平台可能会验证多个cookie的组合。

```python
# services/playwright_mgr.py:234-237
# 按调研文档建议：保存全部cookies，不要精简！
# 因为各平台可能会验证多个cookie的组合
cookies_to_save = all_cookies
logger.info(f"[授权确认] 登录验证通过，保存全部 {len(cookies_to_save)} 个cookies")
```

### 3.3 登录验证关键cookie

只检查最核心的关键cookie来判断是否登录成功：

```python
# services/playwright_mgr.py:212-217
platform_login_check_cookies = {
    "zhihu": ["z_c0"],           # 知乎：z_c0是登录成功凭证，最核心！
    "baijiahao": ["BDUSS"],      # 百家号：BDUSS是百度统一登录凭证，最核心！
    "sohu": ["SUV"],             # 搜狐：SUV是唯一设备标识
    "toutiao": ["sessionid"],    # 头条：sessionid会话ID
}
```

### 3.4 严格登录验证

所有关键cookies必须存在：

```python
# services/playwright_mgr.py:226-232
missing_cookies = [name for name in required_cookies if name not in cookie_names]
if missing_cookies:
    return f'{{"success": false, "message": "未检测到登录信息，请先在平台完成登录！缺少关键cookie: {missing_str}"}}'
```

### 3.4 数据库会话处理

`get_db()` 是生成器函数，需要用 `next()` 获取实际会话：

```python
# services/playwright_mgr.py:75-80
def _get_db(self) -> Optional[Session]:
    if self._db_factory:
        return next(self._db_factory())  # 必须用next()!
    return None
```

---

## 四、本地控制页 (auth_confirm.html)

### 4.1 UI设计

- 紫色渐变背景 (`#667eea` → `#764ba2`)
- 红色授权按钮 (`#ff4d4f`)
- 三步操作指引
- 实时状态显示

### 4.2 关键代码

```javascript
// 检查暴露的函数是否存在
if (typeof window.confirmAuth !== 'function') {
    throw new Error('授权功能未就绪，请刷新页面重试');
}

// 调用Python函数（绕过CORS）
const result = await window.confirmAuth(taskId);
const data = JSON.parse(result);

if (data.success) {
    showStatus('授权信息已保存！账号ID: ' + data.data?.account_id, 'success');
    setTimeout(() => window.close(), 3000);
}
```

---

## 五、API接口

### 5.1 开始授权

```http
POST /api/accounts/auth/start
Content-Type: application/json

{
  "platform": "zhihu",
  "account_name": "我的知乎账号"
}
```

**响应**：
```json
{
  "success": true,
  "message": "授权任务已创建",
  "data": {
    "task_id": "uuid-string",
    "platform": "zhihu",
    "login_url": "https://www.zhihu.com/signin"
  }
}
```

### 5.2 确认授权

```http
POST /api/accounts/auth/confirm/{task_id}
```

**响应**：
```json
{
  "success": true,
  "message": "授权成功！账号已保存",
  "data": {
    "account_id": 1,
    "platform": "zhihu",
    "cookies_count": 2
  }
}
```

---

## 六、测试说明

### 6.1 单元测试

```bash
cd backend
python test_auth_unit.py
```

**测试用例**：
1. 数据库连接测试
2. 加密解密功能测试
3. Playwright初始化测试
4. 授权任务创建测试
5. Cookie提取模拟测试

### 6.2 手动测试

```bash
cd backend
python test_auth.py
```

**测试步骤**：
1. 浏览器自动打开，有两个标签页
2. 在第一个标签页（知乎）完成登录
3. 切换到第二个标签页（紫色控制页）
4. 点击"完成授权"按钮
5. 验证结果并自动关闭浏览器

### 6.3 测试验证点

| 验证项 | 预期结果 |
|-------|---------|
| 未登录点击授权 | 提示"缺少关键cookie" |
| 登录后点击授权 | 保存成功，自动关闭浏览器 |
| 保存的cookies | 只包含关键登录cookies |
| 数据库记录 | cookies字段为加密数据 |

---

## 七、已知问题与修复历史

| 时间 | 问题 | 修复方案 |
|-----|------|---------|
| 2026-01-09 | CORS限制 | 使用`expose_function`绕过 |
| 2026-01-09 | 函数名冲突 | 重命名为`onConfirmButtonClick` |
| 2026-01-09 | 数据库generator错误 | 使用`next()`获取会话 |
| 2026-01-09 | 未登录也能授权 | 添加关键cookie验证 |
| 2026-01-09 | 浏览器不关闭 | 添加`context.close()` |
| 2026-01-09 | 语法错误 | 修复`baijiahao:`缺少冒号 |
| 2026-01-09 | 与调研文档不一致 | **改为保存全部cookies，登录验证只查关键cookie** |

---

## 八、安全说明

1. **加密存储**：所有cookies使用AES-256加密后存储
2. **密钥管理**：密钥存储在环境变量或配置文件中
3. **本地控制页**：使用file://协议，不暴露到公网
4. **会话隔离**：每个授权任务使用独立的BrowserContext

---

## 九、后续优化建议

1. [ ] 支持更多平台（小红书、B站等）
2. [ ] 自动检测登录状态变化，自动完成授权
3. [ ] Cookie过期自动刷新机制
4. [ ] 批量授权多个账号
5. [ ] 二维码登录支持

---

**文档维护**：开发者
**最后更新**：2026-01-09
