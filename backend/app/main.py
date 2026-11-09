from fastapi import FastAPI
from app.api.health import router

app = FastAPI(title="期末复习助手 API")
app.include_router(router, prefix="/api/v1")
