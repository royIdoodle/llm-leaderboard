# 快速开始指南

## 1. 配置数据库（使用 MySQL）

创建 `.env` 文件：

```bash
cp env.example .env
```

编辑 `.env`，参考你的项目格式：

```env
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=llm_leaderboard
MYSQL_USER=root
MYSQL_PASSWORD=6328158Rnnn
```

## 2. 启动服务

```bash
# 一键启动（推荐）
bash scripts/run_dev.sh

# 或手动启动
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 3. 采集数据

### 采集今天的数据
```bash
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all"
```

### 采集指定日期（例如 2024-10-30）
```bash
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-30"
```

### 重新采集同一天（会覆盖之前的数据）
```bash
# 第一次采集 10-30
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-30"
# 返回: inserted=166, updated=0

# 再次采集 10-30（覆盖）
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-30"
# 返回: inserted=0, updated=166
```

## 4. 查询数据

### 查看所有榜单
```bash
# Terminal-Bench
curl "http://127.0.0.1:8000/api/benches/terminal-bench/models"

# OSWorld
curl "http://127.0.0.1:8000/api/benches/osworld/models"
```

### 按组织查询
```bash
curl "http://127.0.0.1:8000/api/query?org=OpenAI"
```

### 按模型跨榜单查询
```bash
curl "http://127.0.0.1:8000/api/models/claude-sonnet-4-5/benches"
```

## 5. 访问页面

- 静态页面：http://127.0.0.1:8000/
- API 文档：http://127.0.0.1:8000/docs

## 核心特性

### ✅ 按天去重
- 每次爬取记录 `scraped_date`（爬取日期）
- 同一天的数据（bench + rank + agent + model + date）唯一
- 重新爬取同一天会**覆盖**旧数据，不会重复

### ✅ 环境变量配置
- 支持 SQLite / MySQL / PostgreSQL
- 参考你的项目格式：`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DB`, `MYSQL_USER`, `MYSQL_PASSWORD`

### ✅ 多维查询
- 按榜单、模型、组织、国家查询
- 支持跨榜单聚合

## 验证测试

```bash
bash scripts/verify.sh
```

## 常见问题

### Q: 如何补采历史数据？
```bash
# 补采 10 月份的数据
for day in {1..31}; do
  curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-$day"
  sleep 5
done
```

### Q: 如何查看数据库中的数据？
```bash
# SQLite
sqlite3 llm_leaderboard.db "SELECT scraped_date, COUNT(*) FROM results GROUP BY scraped_date;"

# MySQL
mysql -u root -p -e "USE llm_leaderboard; SELECT scraped_date, COUNT(*) FROM results GROUP BY scraped_date;"
```

### Q: 如何定时采集？
```bash
# 添加到 crontab（每天凌晨 1 点）
0 1 * * * cd /path/to/llm-leaderboard && .venv/bin/python -m app.cli all
```

## 更多文档

- [README.md](README.md) - 完整文档
- [SUMMARY.md](SUMMARY.md) - 功能总结
- [docs/mysql_setup.md](docs/mysql_setup.md) - MySQL 配置详解

