# 期末复习助手 · 后端

## 启动

在 PowerShell 里，先进入 backend 文件夹，然后：

.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

## 第一次建表（只敲一次）

.venv\Scripts\python.exe -c "from app.db.check import engine; from app.db.models import Base; Base.metadata.create_all(engine)"

## 打开

- 接口列表：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/v1/health
