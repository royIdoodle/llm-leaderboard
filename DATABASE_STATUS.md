# 数据库状态报告

## ✅ 当前数据状态

### 数据库信息
- **类型**: SQLite
- **文件**: `llm_leaderboard.db` (476 KB)
- **位置**: `/Users/wangchong/works/trae-code/llm-leaderboard/`

### 数据统计

**总记录数**: **497 条**

#### 按榜单分布
- Terminal-Bench: **275 条**
- OSWorld: **222 条**

#### 按日期分布
| 日期 | Terminal-Bench | OSWorld | 合计 |
|------|----------------|---------|------|
| 2024-10-30 | 55 | 0 | 55 |
| 2024-10-31 | 55 | 0 | 55 |
| 2024-11-01 | 55 | 111 | 166 |
| 2024-11-02 | 55 | 0 | 55 |
| 2025-10-31 | 55 | 111 | 166 |

#### Top 5 模型
1. claude-sonnet-4: 60 条
2. claude-sonnet-4-5: 30 条
3. agent s3 w/ GPT-5 bBoN (N=1): 20 条
4. claude-opus-4: 20 条
5. opencua-32b: 18 条

## 🔍 如何查看数据

### 方式一：使用查看脚本（推荐）
```bash
python scripts/check_data.py
```

### 方式二：使用 SQLite 命令行
```bash
sqlite3 llm_leaderboard.db "
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
# 查看 Terminal-Bench
curl http://127.0.0.1:8000/api/benches/terminal-bench/models | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"Terminal-Bench: {d['total']} 条\")"

# 查看 OSWorld
curl http://127.0.0.1:8000/api/benches/osworld/models | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"OSWorld: {d['total']} 条\")"
```

### 方式四：使用 Navicat（需要迁移到 MySQL）

**当前使用的是 SQLite，Navicat 无法直接连接。**

如需使用 Navicat 查看，请按以下步骤迁移到 MySQL：

## 📦 迁移到 MySQL（用于 Navicat）

### 快速迁移步骤

1. **创建 MySQL 数据库**
   ```bash
   mysql -u root -p6328158Rnnn -e "CREATE DATABASE llm_leaderboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
   ```

2. **更新 .env 配置**
   ```env
   DB_TYPE=mysql
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_DB=llm_leaderboard
   MYSQL_USER=root
   MYSQL_PASSWORD=6328158Rnnn
   ```

3. **运行迁移脚本**
   ```bash
   python scripts/init_db_and_migrate.py
   ```
   
   脚本会：
   - ✓ 创建 MySQL 表结构
   - ✓ 自动检测 SQLite 数据
   - ✓ 询问是否迁移
   - ✓ 迁移全部 497 条记录

4. **重启服务**
   ```bash
   pkill -f "uvicorn app.main:app"
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

5. **使用 Navicat 连接**
   - 主机: localhost
   - 端口: 3306
   - 用户名: root
   - 密码: 6328158Rnnn
   - 数据库: llm_leaderboard

### 详细迁移指南

请查看：[MIGRATE_TO_MYSQL.md](MIGRATE_TO_MYSQL.md)

## 🛠️ 可用脚本

| 脚本 | 功能 | 用法 |
|------|------|------|
| `check_data.py` | 查看数据统计 | `python scripts/check_data.py` |
| `init_db_and_migrate.py` | 初始化数据库并迁移 | `python scripts/init_db_and_migrate.py` |
| `setup_mysql.sh` | 创建 MySQL 数据库 | `bash scripts/setup_mysql.sh` |

## ✨ 数据完整性验证

### 验证 1: 按天去重
```bash
# 同一天重复采集会覆盖
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=terminal-bench&date=2024-11-02"
# 第一次: inserted=55, updated=0
# 第二次: inserted=0, updated=55 ✓
```

### 验证 2: 数据查询
```bash
# Terminal-Bench 总数
curl http://127.0.0.1:8000/api/benches/terminal-bench/models | python3 -c "import sys,json;print(json.load(sys.stdin)['total'])"
# 输出: 275 ✓

# OSWorld 总数
curl http://127.0.0.1:8000/api/benches/osworld/models | python3 -c "import sys,json;print(json.load(sys.stdin)['total'])"
# 输出: 222 ✓
```

### 验证 3: 多维查询
```bash
# 查询 OpenAI 相关数据
curl "http://127.0.0.1:8000/api/query?org=OpenAI" | python3 -c "import sys,json;print(json.load(sys.stdin)['total'])"
# 输出: 25 ✓
```

## 📊 数据库表结构

```sql
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bench TEXT NOT NULL,  -- 'terminal-bench' 或 'osworld'
    rank INTEGER,
    agent TEXT,
    model TEXT,
    org TEXT,
    org_country TEXT,
    agent_org TEXT,
    model_org TEXT,
    score REAL,
    score_error REAL,
    date TEXT,
    raw_json TEXT,
    scraped_date DATE NOT NULL,  -- 爬取日期（用于去重）
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    
    -- 唯一索引：同一天的相同记录唯一
    UNIQUE(bench, rank, agent, model, scraped_date)
);
```

## 🎯 总结

✅ **数据已成功存储在数据库中**
- SQLite 文件: `llm_leaderboard.db`
- 总记录数: 497 条
- 数据完整性: 已验证
- 按天去重: 正常工作

✅ **如需使用 Navicat 查看**
- 按照 [MIGRATE_TO_MYSQL.md](MIGRATE_TO_MYSQL.md) 迁移到 MySQL
- 或使用其他工具查看 SQLite（如 DB Browser for SQLite）

✅ **推荐工具**
- 开发/测试: SQLite + `check_data.py` 脚本
- 生产环境: MySQL + Navicat
- 跨平台: PostgreSQL + pgAdmin

