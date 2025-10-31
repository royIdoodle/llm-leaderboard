# 项目功能总结

## ✅ 已完成功能

### 1. 数据库配置（环境变量）

- ✅ 支持通过 `.env` 文件配置数据库连接
- ✅ 支持三种数据库类型：
  - SQLite（默认，无需额外配置）
  - MySQL（参考你的项目格式）
  - PostgreSQL
- ✅ 配置格式：
  ```env
  DB_TYPE=mysql
  MYSQL_HOST=localhost
  MYSQL_PORT=3306
  MYSQL_DB=llm_leaderboard
  MYSQL_USER=root
  MYSQL_PASSWORD=your_password
  ```

### 2. 按天去重机制

- ✅ 每条记录包含 `scraped_date` 字段（爬取日期）
- ✅ 唯一索引：`bench + rank + agent + model + scraped_date`
- ✅ 同一天重新爬取会**覆盖**之前的数据，不会重复插入
- ✅ 不同天的数据会独立存储

**示例：**
```bash
# 第一次爬取 2024-10-30
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-30"
# 返回: inserted=166, updated=0

# 再次爬取 2024-10-30（覆盖）
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-30"
# 返回: inserted=0, updated=166

# 爬取 2024-10-31（新数据）
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-31"
# 返回: inserted=166, updated=0
```

### 3. 数据爬取

- ✅ Terminal-Bench 爬虫
  - 数据源：https://www.tbench.ai/leaderboard
  - 使用 XPath 解析 HTML 表格
  - 提取：rank, agent, model, org, score (Accuracy)
  
- ✅ OSWorld 爬虫
  - 数据源：https://os-world.github.io/
  - 解析 Excel 文件（osworld_verified_results.xlsx）
  - 提取：rank, model, approach, org, score (Success Rate)

### 4. API 接口

#### 采集接口
```bash
# 采集今天的数据
POST /api/scrape?bench=all

# 采集指定日期的数据
POST /api/scrape?bench=terminal-bench&date=2024-10-30
```

#### 查询接口
```bash
# 按榜单查询
GET /api/benches/terminal-bench/models
GET /api/benches/osworld/models

# 按模型跨榜单查询
GET /api/models/claude-sonnet-4-5/benches

# 多维查询
GET /api/query?bench=terminal-bench,osworld&org=OpenAI&nation=United%20States
```

### 5. 数据字段

| 字段 | 说明 | 来源 |
|------|------|------|
| bench | 榜单类型 | terminal-bench / osworld |
| rank | 排名 | 榜单数据 |
| agent | Agent 名称 | 榜单数据 |
| model | 模型名称 | 榜单数据 |
| org | 组织 | 榜单数据（Agent Org 优先） |
| nation | 国家 | org_countries.yaml 映射 |
| score | 分数 | Terminal-Bench: Accuracy / OSWorld: Success Rate |
| scraped_date | 爬取日期 | 系统生成（用于去重） |

### 6. 组织-国家映射

- ✅ 配置文件：`data/org_countries.yaml`
- ✅ 大小写不敏感
- ✅ 支持动态更新
- ✅ 未配置的组织返回 `null`

### 7. 静态页面

- ✅ 数据展示页面：http://127.0.0.1:8000/
- ✅ 支持触发采集
- ✅ 实时显示两个榜单数据

### 8. 部署与运维

- ✅ 一键启动脚本：`bash scripts/run_dev.sh`
- ✅ 验证脚本：`bash scripts/verify.sh`
- ✅ CLI 工具：`python -m app.cli all`
- ✅ 完整文档：README.md

## 🎯 核心特性

### 按天去重的优势

1. **历史数据保留**：可以查看不同日期的榜单变化
2. **避免重复**：同一天多次爬取不会产生重复数据
3. **数据覆盖**：同一天重新爬取会更新数据，保证数据最新
4. **灵活查询**：可以按日期范围查询历史数据

### 数据库设计亮点

1. **复合唯一索引**：确保数据唯一性
2. **自动时间戳**：created_at / updated_at 自动维护
3. **多数据库支持**：SQLite / MySQL / PostgreSQL
4. **环境变量配置**：灵活切换数据库

## 📊 测试结果

### 功能测试

```bash
# 测试 1：首次采集
✓ 2024-10-30: inserted=55, updated=0

# 测试 2：重复采集（覆盖）
✓ 2024-10-30: inserted=0, updated=55

# 测试 3：新日期采集
✓ 2024-10-31: inserted=55, updated=0

# 测试 4：数据库验证
✓ 2024-10-30: 55 条
✓ 2024-10-31: 55 条
✓ 2024-11-01: 166 条
```

### API 测试

```bash
✓ 健康检查通过
✓ Terminal-Bench 采集成功（55 条）
✓ OSWorld 采集成功（111 条）
✓ 多维查询正常
✓ 跨榜单查询正常
```

## 📝 使用示例

### 场景 1：每日定时采集

```bash
# 使用 cron 每天凌晨 1 点采集
0 1 * * * cd /path/to/llm-leaderboard && .venv/bin/python -m app.cli all
```

### 场景 2：补采历史数据

```bash
# 补采 10 月 1 日到 10 月 31 日的数据
for day in {1..31}; do
  date=$(printf "2024-10-%02d" $day)
  curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=$date"
  sleep 5
done
```

### 场景 3：查询趋势

```python
from app.db import SessionLocal
from app.models import Result
from sqlalchemy import select

with SessionLocal() as session:
    # 查询某个模型在不同日期的分数变化
    stmt = select(Result).where(
        Result.model == "claude-sonnet-4-5",
        Result.bench == "terminal-bench"
    ).order_by(Result.scraped_date)
    
    results = session.execute(stmt).scalars().all()
    for r in results:
        print(f"{r.scraped_date}: rank={r.rank}, score={r.score}")
```

## 🔧 环境变量配置示例

### SQLite（开发环境）
```env
DB_TYPE=sqlite
SQLITE_DB_PATH=llm_leaderboard.db
```

### MySQL（生产环境）
```env
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=llm_leaderboard
MYSQL_USER=root
MYSQL_PASSWORD=your_password
```

### PostgreSQL（企业环境）
```env
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=llm_leaderboard
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

## 📚 相关文档

- [README.md](README.md) - 项目说明与快速开始
- [docs/mysql_setup.md](docs/mysql_setup.md) - MySQL 配置指南
- [env.example](env.example) - 环境变量模板

## ✨ 技术栈

- **后端框架**：FastAPI 0.115+
- **数据库 ORM**：SQLAlchemy 2.0+
- **爬虫**：requests + lxml + openpyxl
- **数据库**：SQLite / MySQL / PostgreSQL
- **部署**：Uvicorn

