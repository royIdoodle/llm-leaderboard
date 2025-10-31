# 按天去重机制详解

## 设计原理

本系统采用**按天去重**的设计，每天的数据是独立存储的，同一天的数据会被覆盖。

### 唯一性约束

数据库中有唯一索引：
```sql
UNIQUE INDEX (bench, rank, agent, model, scraped_date)
```

这意味着：**同一天（scraped_date）+ 同一榜单（bench）+ 同一排名（rank）+ 同一 agent + 同一 model** 的记录是唯一的。

## 工作方式

### 场景 1：不指定日期（默认今天）

```bash
# 第一次调用（假设今天是 2024-12-01）
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all"
# 结果: inserted=166, updated=0
# 数据库: 2024-12-01 有 166 条数据

# 第二次调用（同一天）
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all"
# 结果: inserted=0, updated=166
# 数据库: 2024-12-01 仍然只有 166 条数据 ✅

# 第二天调用（2024-12-02）
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all"
# 结果: inserted=166, updated=0
# 数据库: 2024-12-01 有 166 条，2024-12-02 有 166 条 ✅
```

### 场景 2：指定日期

```bash
# 采集 2024-10-30 的数据
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-30"
# 结果: inserted=166, updated=0

# 再次采集 2024-10-30（即使过了很多天）
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-10-30"
# 结果: inserted=0, updated=166
# 数据库: 2024-10-30 仍然只有 166 条数据 ✅
```

## 验证去重是否正常

### 方法 1：使用脚本测试

```bash
python << 'EOF'
from datetime import date
from app.services.ingest import ingest

print("第一次采集:")
i1, u1, t1 = ingest('terminal-bench', date(2024, 12, 1))
print(f"inserted={i1}, updated={u1}")

print("\n第二次采集（应该全部更新）:")
i2, u2, t2 = ingest('terminal-bench', date(2024, 12, 1))
print(f"inserted={i2}, updated={u2}")

if i2 == 0 and u2 == t2:
    print("\n✅ 去重正常")
else:
    print("\n❌ 去重异常")
EOF
```

### 方法 2：查询数据库

```bash
# 查看某个日期的数据条数
mysql -u root -p llm_leaderboard -e "
SELECT scraped_date, bench, COUNT(*) as count
FROM results
WHERE scraped_date = '2024-12-01'
GROUP BY scraped_date, bench;"

# 如果多次采集后，count 仍然是 55（Terminal-Bench）或 111（OSWorld），说明去重正常
```

### 方法 3：使用 API

```bash
# 第一次采集
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=terminal-bench&date=2024-12-01"
# 返回: {"inserted":55,"updated":0,"total":55}

# 第二次采集
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=terminal-bench&date=2024-12-01"
# 返回: {"inserted":0,"updated":55,"total":55}
# ✅ inserted=0 说明没有重复插入
```

## 常见误解

### ❌ 误解 1："每次采集数据都重复了"

**原因**：可能是不同天的采集，每天都应该有独立的数据。

**验证**：
```bash
# 查看所有日期的数据
mysql -u root -p llm_leaderboard -e "
SELECT scraped_date, COUNT(*) as count
FROM results
GROUP BY scraped_date
ORDER BY scraped_date;"
```

如果看到多个日期，这是**正常的**，因为每天都应该保留独立的数据。

### ❌ 误解 2："查询时看到很多重复数据"

**原因**：查询时没有按日期过滤。

**示例**：
```bash
# 错误的查询（会返回所有日期的数据）
SELECT * FROM results WHERE model = 'claude-sonnet-4-5';
# 可能返回 30 条（5 个日期 × 6 条/日期）

# 正确的查询（只查询最新日期）
SELECT * FROM results 
WHERE model = 'claude-sonnet-4-5' 
  AND scraped_date = (SELECT MAX(scraped_date) FROM results);
# 返回 6 条
```

## 数据管理

### 只保留最新数据

如果你只想保留最新一天的数据，可以使用清理脚本：

```bash
python scripts/clean_old_data.py
# 选择 "1. 只保留最新日期的数据"
```

### 删除指定日期的数据

```bash
python scripts/clean_old_data.py
# 选择 "2. 删除指定日期的数据"
# 输入日期: 2024-10-30
```

### 手动清理

```bash
# 删除 2024-11-01 之前的所有数据
mysql -u root -p llm_leaderboard -e "
DELETE FROM results WHERE scraped_date < '2024-11-01';"

# 只保留最新 7 天的数据
mysql -u root -p llm_leaderboard -e "
DELETE FROM results 
WHERE scraped_date < DATE_SUB(CURDATE(), INTERVAL 7 DAY);"
```

## 推荐使用方式

### 方式 1：每日定时采集（推荐）

```bash
# 添加到 crontab
0 1 * * * curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all"
```

- 每天凌晨 1 点自动采集
- 自动使用当天日期
- 保留历史数据，可以看到榜单变化趋势

### 方式 2：只保留最新数据

```bash
# 采集前先清理旧数据
python scripts/clean_old_data.py  # 选择 1

# 然后采集
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all"
```

- 数据库只保留最新一天的数据
- 节省存储空间
- 无法查看历史趋势

### 方式 3：固定日期采集

```bash
# 始终使用固定日期（如 2024-01-01）
curl -X POST "http://127.0.0.1:8000/api/scrape?bench=all&date=2024-01-01"
```

- 每次采集都覆盖同一天的数据
- 数据库只有一个日期的数据
- 适合只关心当前状态，不关心历史

## 查询最新数据

### API 查询（自动返回所有日期）

```bash
# 查询所有日期的 Terminal-Bench 数据
curl "http://127.0.0.1:8000/api/benches/terminal-bench/models"
```

### 只查询最新日期

如果你只想看最新日期的数据，可以在 API 中添加日期过滤：

```bash
# 先获取最新日期
LATEST_DATE=$(mysql -u root -p6328158Rnnn llm_leaderboard -se "SELECT MAX(scraped_date) FROM results;")

# 查询最新日期的数据
curl "http://127.0.0.1:8000/api/query?bench=terminal-bench&date=$LATEST_DATE"
```

## 总结

✅ **按天去重是正常工作的**
- 同一天多次采集 → 覆盖
- 不同天采集 → 新增

✅ **如果觉得数据重复**
- 检查是否不同天的采集
- 查询时是否需要按日期过滤
- 使用清理脚本删除旧数据

✅ **推荐做法**
- 每日定时采集，保留历史数据
- 或者采集前清理旧数据，只保留最新
- 查询时明确是否需要过滤日期

