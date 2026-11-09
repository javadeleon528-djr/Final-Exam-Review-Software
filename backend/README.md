# 期末复习助手 · 后端

需要 Python 3.10 或更高版本。以下命令都在 `backend` 文件夹下执行。

## 第一次准备（新电脑）

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
mkdir data
.\.venv\Scripts\python.exe -m alembic upgrade head

`upgrade head` 按 `alembic/versions/` 里的记录建出 `courses` 表。
数据库文件是 `data/study.db`，已被 `.gitignore` 排除，不会提交到 Git。

## 启动

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

## 打开

- 接口列表：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/v1/health

健康检查会确认 `courses` 表存在；没跑迁移或数据库不可用时返回 503 `STORAGE_ERROR`。

