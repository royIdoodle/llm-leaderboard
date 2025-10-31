#!/usr/bin/env bash
set -euo pipefail
BASE="http://127.0.0.1:8000"

echo "=== LLM Leaderboard 验证脚本 ==="
echo ""

echo "[1/6] 健康检查..."
curl -fsS "$BASE/api/health" >/dev/null || { echo "❌ 健康检查失败"; exit 1; }
echo "✓ 健康检查通过"

echo ""
echo "[2/6] 触发数据采集..."
SCRAPE_RESULT=$(curl -fsS -X POST "$BASE/api/scrape?bench=all")
echo "$SCRAPE_RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'✓ 采集完成: 新增={d[\"inserted\"]}, 更新={d[\"updated\"]}, 总数={d[\"total\"]}')"

echo ""
echo "[3/6] 查询 Terminal-Bench 榜单..."
TB_RESULT=$(curl -fsS "$BASE/api/benches/terminal-bench/models")
echo "$TB_RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'✓ Terminal-Bench: {d[\"total\"]} 条记录')"

echo ""
echo "[4/6] 查询 OSWorld 榜单..."
OSW_RESULT=$(curl -fsS "$BASE/api/benches/osworld/models")
echo "$OSW_RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'✓ OSWorld: {d[\"total\"]} 条记录')"

echo ""
echo "[5/6] 测试多维查询（按组织过滤）..."
QUERY_RESULT=$(curl -fsS "$BASE/api/query?org=OpenAI")
echo "$QUERY_RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'✓ OpenAI 相关记录: {d[\"total\"]} 条')"

echo ""
echo "[6/6] 测试跨榜单查询（按模型）..."
MODEL_RESULT=$(curl -fsS "$BASE/api/models/claude-sonnet-4-5/benches")
echo "$MODEL_RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'✓ claude-sonnet-4-5 跨榜单: {d[\"total\"]} 条记录')"

echo ""
echo "==================================="
echo "✅ 所有验证通过！"
echo "==================================="
echo ""
echo "访问地址："
echo "  - 静态页面: $BASE/"
echo "  - API 文档: $BASE/docs"
echo ""
