import os
import uuid
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal, ensure_schema
import app.models # Register all models

from app.api.v1 import (
    auth, public, jobs, resumes, applications,
    personal, interviews, enterprise, admin, files, external_applications, realtime, job_search
)
from app.websocket.interview_ws import handle_interview_websocket
from app.websocket.notification_ws import handle_notification_websocket
from app.services.interview_sweeper import run_zombie_sweeper_loop

# Create database tables automatically
# Lightweight incremental migration for columns added after initial release
ensure_schema()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 模拟面试不限制提交时间（D6），关页面遗留的进行中场次由后台任务兜底收尾
    sweeper = asyncio.create_task(run_zombie_sweeper_loop())
    yield
    sweeper.cancel()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="经纬职引-智面仓 AI Interview Hub 全栈后端 API 系统",
    version="3.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials="*" not in settings.BACKEND_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads static directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.add_api_route("/uploads/{object_key}", files.download_file, methods=["GET"])

# Include API v1 Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(public.router, prefix=api_v1_prefix)
app.include_router(jobs.router, prefix=api_v1_prefix)
app.include_router(resumes.router, prefix=api_v1_prefix)
app.include_router(applications.router, prefix=api_v1_prefix)
app.include_router(personal.router, prefix=api_v1_prefix)
app.include_router(interviews.router, prefix=api_v1_prefix)
app.include_router(enterprise.router, prefix=api_v1_prefix)
app.include_router(admin.router, prefix=api_v1_prefix)
app.include_router(files.router, prefix=api_v1_prefix)
app.include_router(external_applications.router, prefix=api_v1_prefix)
app.include_router(realtime.router, prefix=api_v1_prefix)
app.include_router(job_search.router, prefix=api_v1_prefix)

@app.middleware("http")
async def trace_request(request: Request, call_next):
    from app.services.ai_provenance import ai_context
    from app.core.security import decode_token
    request_id = uuid.uuid4().hex
    raw = request.headers.get("Authorization", "")
    claims = decode_token(raw[7:]) if raw.startswith("Bearer ") else None
    try:
        user_id = int(claims["sub"]) if claims else None
    except (ValueError, KeyError, TypeError):
        user_id = None
    with ai_context(user_id=user_id, request_id=request_id):
        response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health():
    from sqlalchemy import text
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "healthy"}


# WebSocket interview room endpoint
@app.websocket("/ws/interviews/{interview_id}")
async def websocket_interview_endpoint(websocket: WebSocket, interview_id: int):
    await handle_interview_websocket(websocket, interview_id)

# WebSocket notification push endpoint
@app.websocket("/ws/notifications/{user_id}")
async def websocket_notification_endpoint(websocket: WebSocket, user_id: int):
    await handle_notification_websocket(websocket, user_id)

# Global Exception Handler to ensure standard response structure {code, message, data}
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.getLogger("backend").error("请求处理失败 %s", request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误，请稍后重试", "data": None}
    )

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "3.0.0",
        "status": "online",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
