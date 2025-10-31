#!/usr/bin/env bash
set -e

echo "========================================="
echo "  MySQL 数据库初始化脚本"
echo "========================================="
echo ""

# 读取配置
MYSQL_HOST=${MYSQL_HOST:-localhost}
MYSQL_PORT=${MYSQL_PORT:-3306}
MYSQL_USER=${MYSQL_USER:-root}
MYSQL_PASSWORD=${MYSQL_PASSWORD}
MYSQL_DB=${MYSQL_DB:-llm_leaderboard}

if [ -z "$MYSQL_PASSWORD" ]; then
    echo "请输入 MySQL 密码："
    read -s MYSQL_PASSWORD
    echo ""
fi

echo "配置信息："
echo "  Host: $MYSQL_HOST"
echo "  Port: $MYSQL_PORT"
echo "  User: $MYSQL_USER"
echo "  Database: $MYSQL_DB"
echo ""

# 检查 MySQL 连接
echo "1. 检查 MySQL 连接..."
mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SELECT VERSION();" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ MySQL 连接成功"
else
    echo "   ✗ MySQL 连接失败，请检查配置"
    exit 1
fi

# 创建数据库
echo ""
echo "2. 创建数据库 $MYSQL_DB..."
mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" <<EOF
CREATE DATABASE IF NOT EXISTS $MYSQL_DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF
echo "   ✓ 数据库创建成功"

# 检查数据库是否存在
echo ""
echo "3. 验证数据库..."
DB_EXISTS=$(mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SHOW DATABASES LIKE '$MYSQL_DB';" | grep -c "$MYSQL_DB" || true)
if [ "$DB_EXISTS" -eq 1 ]; then
    echo "   ✓ 数据库 $MYSQL_DB 已存在"
else
    echo "   ✗ 数据库创建失败"
    exit 1
fi

echo ""
echo "========================================="
echo "  ✅ MySQL 数据库初始化完成！"
echo "========================================="
echo ""
echo "下一步："
echo "1. 更新 .env 文件，设置 DB_TYPE=mysql 和你的密码"
echo "2. 重启服务，表结构会自动创建"
echo "3. 调用采集接口导入数据"
echo ""

