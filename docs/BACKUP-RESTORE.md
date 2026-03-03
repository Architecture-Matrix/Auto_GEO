# AutoGeo 数据备份与恢复

## 备份策略

### 数据位置

```
~/autogeo/                  # 服务器上的数据目录
├── database/               # SQLite 数据库 (最重要！)
│   └── auto_geo_v3.db
├── cookies/                # 登录状态 (重要！)
├── data/                   # 其他数据
└── logs/                   # 日志 (可选备份)
```

### 备份方式

| 方式 | 频率 | 保留时间 | 说明 |
|-----|------|---------|------|
| **每日备份** | 每天 | 7天 | 脚本自动清理旧备份 |
| **手动备份** | 按需 | 永久 | 重大操作前手动备份 |
| **云同步** | 实时 | - | 可选：同步到阿里云OSS |

---

## 使用方法

### Linux/macOS 服务器

#### 1. 上传备份脚本

```bash
# 上传脚本到服务器
scp scripts/backup-autogeo.sh user@server:/usr/local/bin/
ssh user@server "chmod +x /usr/local/bin/backup-autogeo.sh"
```

#### 2. 手动备份

```bash
# 执行备份
/usr/local/bin/backup-autogeo.sh

# 备份存储位置
/autogeo-backup/daily/
```

#### 3. 设置定时备份（推荐）

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 3 点备份
0 3 * * * /usr/local/bin/backup-autogeo.sh >> /var/log/autogeo-backup.log 2>&1
```

#### 4. 恢复数据

```bash
# 查看可用备份
ls -lh /autogeo-backup/daily/

# 恢复指定日期的备份
/usr/local/bin/restore-autogeo.sh 20260226

# 恢复指定的备份文件
/usr/local/bin/restore-autogeo.sh auto_geo_v3_20260226_030000.db
```

### Windows 本地

```cmd
# 运行备份脚本
scripts\backup-autogeo.bat

# 备份存储位置
C:\autogeo-backup\daily\
```

---

## 快速备份命令（服务器上直接执行）

### 备份数据库

```bash
# 简单粗暴：直接复制
cp ~/autogeo/database/auto_geo_v3.db ~/autogeo/database/auto_geo_v3_$(date +%Y%m%d).db

# 或者使用 SQLite 在线备份（容器运行中）
docker exec autogeo-backend sqlite3 /app/database/auto_geo_v3.db ".backup /app/database/auto_geo_v3_$(date +%Y%m%d).db"
```

### 备份 Cookies

```bash
tar -czf ~/cookies_backup_$(date +%Y%m%d).tar.gz -C ~/autogeo cookies/
```

### 打包整个数据目录

```bash
tar -czf ~/autogeo_backup_$(date +%Y%m%d).tar.gz ~/autogeo/
```

---

## 恢复流程

### 从备份恢复数据库

```bash
# 1. 停止容器
docker stop autogeo-backend

# 2. 备份当前数据（防止恢复失败）
cp ~/autogeo/database/auto_geo_v3.db ~/autogeo/database/auto_geo_v3_before_restore.db

# 3. 恢复备份
cp /autogeo-backup/daily/auto_geo_v3_20260226.db ~/autogeo/database/auto_geo_v3.db

# 4. 启动容器
docker start autogeo-backend

# 5. 验证
curl http://localhost:8001/api/health
```

---

## 云备份（可选）

### 阿里云 OSS 上传

```bash
# 安装 ossutil
wget http://gosspublic.alicdn.com/ossutil/1.7.15/ossutil64
chmod +x ossutil64

# 配置
./ossutil64 config

# 上传备份
./ossutil64 cp /autogeo-backup/daily/auto_geo_v3_$(date +%Y%m%d).db oss://your-bucket/autogeo-backups/
```

### rsync 同步到另一台服务器

```bash
# 同步到备份服务器
rsync -avz --delete ~/autogeo/ backup-user@backup-server:/backups/autogeo/
```

---

**建议**:
1. ✅ 每天自动备份（cron）
2. ✅ 重大操作前手动备份
3. ✅ 定期验证备份可用性
4. ✅ 重要数据异地备份
