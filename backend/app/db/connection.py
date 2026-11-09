"""T02 / 同学 B：SQLite 连接与健康检查。

由同学 A 的配置模块传入 database_url；这里不读取前端配置，
也不在函数里固定数据库文件位置。
"""

from sqlalchemy.engine import Engine
from sqlalchemy import create_engine , text
from sqlalchemy.exc import SQLAlchemyError


def make_engine(database_url: str) -> Engine:
    """按传入的数据库 URL 创建 SQLAlchemy Engine。

    第一步由你实现：检查 URL 不为空，再建立 Engine 并返回。
    当前只使用 SQLite；数据库文件路径由调用方决定。
    """
    if not database_url or not database_url.strip():     #`strip()`：去掉前后空格，防止传 `"   "` 这种空白字符串
        raise ValueError("database_url 不能为空")
    # 加强校验
    database_url = database_url.strip()
    if not database_url.startswith("sqlite://"): 
        raise ValueError("只支持 SqLite ,url 开头必须以sqlite:// 的形式")
    # 创建引擎
    engine = create_engine(database_url)
    return engine
    
    

def check_database(engine: Engine) -> bool:
    """执行一次简单查询，连接可用返回 True，不可用返回 False。
    第二步由你实现：打开连接，执行 SELECT 1，连接用完后释放。
    同学 A 会在健康检查接口里调用此函数。
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except SQLAlchemyError:
        return False

