# 迁移到 MySQL 数据库指南

当前数据存储在 SQLite 中（`llm_leaderboard.db`），如果你想使用 Navicat 查看，需要迁移到 MySQL。

## 当前数据状态

✅ SQLite 数据库中已有 **497 条记录**：
- Terminal-Bench: 275 条
- OSWorld: 222 条
- 按日期分布: 2024-10-30 到 2025-10-31

## 迁移步骤

### 1. 准备 MySQL 数据库

#### 方式一：使用脚本（推荐）

```bash
# 设置环境变量
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=6328158Rnnn
export MYSQL_DB=llm_leaderboard

# 运行初始化脚本
bash scripts/setup_mysql.sh
```

#### 方式二：手动创建

登录 MySQL：
```bash
mysql -u root -p
```

创建数据库：
```sql
CREATE DATABASE llm_leaderboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 2. 更新环境变量

编辑 `.env` 文件：

```env
# 修改数据库类型为 mysql
DB_TYPE=mysql

# MySQL 配置（使用你的密码）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=llm_leaderboard
MYSQL_USER=root
MYSQL_PASSWORD=6328158Rnnn
```

### 3. 创建表结构并迁移数据

运行迁移脚本：
```bash
python scripts/init_db_and_migrate.py
```

脚本会：
1. ✓ 在 MySQL 中创建表结构
2. ✓ 检测到 SQLite 数据
3. ✓ 询问是否迁移
4. ✓ 迁移所有 497 条记录到 MySQL

### 4. 重启服务

停止当前服务（Ctrl+C），然后重启：
```bash
pkill -f "uvicorn app.main:app"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. 使用 Navicat 连接

在 Navicat 中新建 MySQL 连接：
- **主机**: localhost
- **端口**: 3306
- **用户名**: root
- **密码**: 6328158Rnnn
- **数据库**: llm_leaderboard

连接后可以看到 `results` 表和所有数据。

## 验证迁移

### 方式一：使用脚本
```bash
python scripts/init_db_and_migrate.py
```

### 方式二：使用 MySQL 命令
```bash
mysql -u root -p6328158Rnnn -e "
USE llm_leaderboard;
SELECT 
    bench,
    scraped_date,
    COUNT(*) as count
FROM results
GROUP BY bench, scraped_date
ORDER BY scraped_date, bench;
"
```

### 方式三：使用 API
```bash
curl http://127.0.0.1:8000/api/benches/terminal-bench/models | python3 -c "import sys,json;print(json.load(sys.stdin)['total'])"
curl http://127.0.0.1:8000/api/benches/osworld/models | python3 -c "import sys,json;print(json.load(sys.stdin)['total'])"
```

## 常见问题

### Q1: 迁移后 SQLite 数据还在吗？
A: 是的，SQLite 文件不会被删除，可以作为备份保留。

### Q2: 可以同时使用两个数据库吗？
A: 不可以，同一时间只能使用一个数据库。通过 `.env` 中的 `DB_TYPE` 切换。

### Q3: 迁移失败怎么办？
A: 检查：
1. MySQL 服务是否运行：`sudo systemctl status mysql`
2. 密码是否正确
3. 数据库是否已创建
4. 用户是否有权限

### Q4: 如何切换回 SQLite？
修改 `.env`：
```env
DB_TYPE=sqlite
SQLITE_DB_PATH=llm_leaderboard.db
```
然后重启服务。

## 表结构

迁移后的 MySQL 表结构：

```sql
CREATE TABLE results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bench ENUM('terminal-bench', 'osworld') NOT NULL,
    rank INT,
    agent VARCHAR(255),
    model VARCHAR(255),
    org VARCHAR(255),
    org_country VARCHAR(128),
    agent_org VARCHAR(255),
    model_org VARCHAR(255),
    score FLOAT,
    score_error FLOAT,
    date VARCHAR(64),
    raw_json TEXT,
    scraped_date DATE NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    
    INDEX idx_bench (bench),
    INDEX idx_rank (rank),
    INDEX idx_agent (agent),
    INDEX idx_model (model),
    INDEX idx_org (org),
    INDEX idx_org_country (org_country),
    INDEX idx_score (score),
    INDEX idx_date (date),
    INDEX idx_scraped_date (scraped_date),
    
    UNIQUE INDEX idx_unique_record (bench, rank, agent, model, scraped_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## 性能对比

| 数据库 | 优点 | 缺点 |
|--------|------|------|
| SQLite | 简单、无需配置、适合开发 | 不支持并发写入、不适合生产 |
| MySQL | 高性能、支持并发、适合生产 | 需要配置、需要单独服务 |

**建议**：
- 开发环境：使用 SQLite
- 生产环境：使用 MySQL 或 PostgreSQL

