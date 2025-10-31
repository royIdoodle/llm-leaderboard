# LLM Leaderboard Scraper

本项目用于爬取与查询两个榜单的数据：
- Terminal-Bench: `https://www.tbench.ai/leaderboard`
- OSWorld-Verified: `https://os-world.github.io/`

功能：
- 爬取上述榜单核心字段（org、nation、model、agent、score）
- 支持 SQLite/MySQL/PostgreSQL 数据库存储
- 按天去重：同一天的数据重新爬取会覆盖之前的记录
- FastAPI 查询接口（多维查询）
- 静态页面验证数据正确性

## 快速开始

### 1. 配置数据库

复制环境变量模板并修改配置：
```bash
cp env.example .env
```

编辑 `.env` 文件，选择数据库类型：

**使用 SQLite（默认，无需额外配置）：**
```env
DB_TYPE=sqlite
SQLITE_DB_PATH=llm_leaderboard.db
```

**使用 MySQL：**
```env
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=llm_leaderboard
MYSQL_USER=root
MYSQL_PASSWORD=your_password
```

**使用 PostgreSQL：**
```env
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=llm_leaderboard
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

### 2. 安装依赖并启动

**方式一：使用一键脚本（推荐）**
```bash
bash scripts/run_dev.sh
```

**方式二：手动启动**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 访问服务

- 静态页面: http://127.0.0.1:8000/
- API 文档: http://127.0.0.1:8000/docs
- 健康检查: http://127.0.0.1:8000/api/health

## 数据采集

### 按天去重机制

- 每次爬取会记录 `scraped_date`（爬取日期）
- 同一天（bench + rank + agent + model + scraped_date）的数据是唯一的
- 重新爬取同一天的数据会**覆盖**之前的记录，不会重复插入

### API 采集

**采集今天的数据：**
```bash
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all"
```

**采集指定日期的数据：**
```bash
# 爬取 2024-10-30 的数据
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-30"

# 再次爬取 2024-10-30 会覆盖之前的数据
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-30"
```

**只采集特定榜单：**
```bash
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=terminal-bench"
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=osworld"
```

### CLI 采集

```bash
# 采集今天的数据
python -m app.cli all

# 采集单个榜单
python -m app.cli terminal-bench
python -m app.cli osworld
```

## API 查询示例

### 按榜单查询
```bash
# 查询 Terminal-Bench 所有模型
GET /api/benches/terminal-bench/models

# 查询 OSWorld 所有模型
GET /api/benches/osworld/models
```

### 按模型跨榜单查询
```bash
# 查询 claude-sonnet-4-5 在所有榜单的排名
GET /api/models/claude-sonnet-4-5/benches
```

### 多维查询
```bash
# 按组织过滤
GET /api/query?org=OpenAI

# 按国家过滤
GET /api/query?nation=United%20States

# 组合查询
GET /api/query?bench=terminal-bench,osworld&org=Anthropic&model=claude-sonnet-4-5
```

## 字段说明

- **org**: 排名中的组织（默认取 Agent Org）
- **nation**: 组织对应国家（通过 `data/org_countries.yaml` 映射）
- **model**: 模型名称
- **agent**: 使用的 Agent 名称
- **score**: 成绩
  - Terminal-Bench: Accuracy (%)
  - OSWorld: Success Rate (%)
- **scraped_date**: 数据爬取日期（用于按天去重）

## 组织-国家映射

在 `data/org_countries.yaml` 中维护组织与国家的映射关系：

```yaml
anthropic: United States
openai: United States
alibaba: China
# ... 更多映射
```

映射规则：
- 大小写不敏感
- 未配置的组织返回 `null`
- 可随时添加新的映射

## 验证测试

运行完整验证脚本：
```bash
bash scripts/verify.sh
```

该脚本会测试：
1. 健康检查
2. 数据采集
3. 榜单查询
4. 多维查询
5. 跨榜单查询

## 项目结构

```
llm-leaderboard/
├── app/
│   ├── main.py              # FastAPI 主程序
│   ├── models.py            # 数据库模型
│   ├── schemas.py           # Pydantic 模式
│   ├── db.py                # 数据库连接
│   ├── cli.py               # 命令行工具
│   ├── scrapers/            # 爬虫模块
│   │   ├── terminal_bench.py
│   │   └── osworld.py
│   ├── services/            # 业务逻辑
│   │   └── ingest.py        # 数据入库
│   └── utils/               # 工具函数
│       └── country.py       # 国家映射
├── data/
│   └── org_countries.yaml   # 组织-国家映射
├── public/
│   └── index.html           # 静态页面
├── scripts/
│   ├── run_dev.sh           # 一键启动脚本
│   └── verify.sh            # 验证脚本
├── env.example              # 环境变量模板
├── requirements.txt         # Python 依赖
└── README.md
```
