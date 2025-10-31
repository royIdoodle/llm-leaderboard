from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_database_url() -> str:
    """根据环境变量构建数据库连接 URL"""
    db_type = os.getenv("DB_TYPE", "sqlite").lower()
    
    if db_type == "sqlite":
        db_path = os.getenv("SQLITE_DB_PATH", "llm_leaderboard.db")
        return f"sqlite:///{db_path}"
    
    elif db_type == "mysql":
        host = os.getenv("MYSQL_HOST", "localhost")
        port = os.getenv("MYSQL_PORT", "3306")
        database = os.getenv("MYSQL_DB", "llm_leaderboard")
        user = os.getenv("MYSQL_USER", "root")
        password = os.getenv("MYSQL_PASSWORD", "")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    
    elif db_type == "postgresql":
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "llm_leaderboard")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    else:
        raise ValueError(f"不支持的数据库类型: {db_type}，支持的类型: sqlite, mysql, postgresql")


# 获取数据库 URL
DATABASE_URL = get_database_url()

# 根据数据库类型设置连接参数
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    future=True,
    pool_pre_ping=True,  # 自动检测连接是否有效
    echo=False,  # 设置为 True 可以看到 SQL 日志
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
