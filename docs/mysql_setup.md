# MySQL 数据库配置指南

## 1. 创建数据库

登录 MySQL 并创建数据库：

```sql
CREATE DATABASE llm_leaderboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 2. 创建用户（可选）

如果需要创建专用用户：

```sql
CREATE USER 'llm_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON llm_leaderboard.* TO 'llm_user'@'localhost';
FLUSH PRIVILEGES;
```

## 3. 配置环境变量

复制 `env.example` 为 `.env` 并修改：

```env
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=llm_leaderboard
MYSQL_USER=root
MYSQL_PASSWORD=your_password
```

## 4. 启动服务

服务启动时会自动创建表结构：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 5. 验证连接

```bash
curl http://127.0.0.1:8000/api/health
```

## 数据库表结构

服务会自动创建以下表：

### results 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| bench | ENUM | 榜单类型（terminal-bench/osworld） |
| rank | INT | 排名 |
| agent | VARCHAR(255) | Agent 名称 |
| model | VARCHAR(255) | 模型名称 |
| org | VARCHAR(255) | 组织 |
| org_country | VARCHAR(128) | 组织国家 |
| agent_org | VARCHAR(255) | Agent 组织 |
| model_org | VARCHAR(255) | 模型组织 |
| score | FLOAT | 分数 |
| score_error | FLOAT | 分数误差 |
| date | VARCHAR(64) | 榜单日期 |
| raw_json | TEXT | 原始数据 JSON |
| scraped_date | DATE | 爬取日期（用于去重） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 唯一索引

- `idx_unique_record`: (bench, rank, agent, model, scraped_date)
  - 确保同一天的相同记录唯一

## 常见问题

### 1. 连接被拒绝

检查 MySQL 服务是否运行：
```bash
sudo systemctl status mysql
```

### 2. 权限不足

确保用户有足够权限：
```sql
SHOW GRANTS FOR 'your_user'@'localhost';
```

### 3. 字符集问题

确保数据库使用 utf8mb4：
```sql
ALTER DATABASE llm_leaderboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

