import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import create_db_and_tables
from app.utils.redis import close_redis
from app.routers import auth, session, style, styles

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PRESETS_DIR = Path(__file__).parent.parent / "presets"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await create_db_and_tables()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    logger.info("Shutting down...")
    await close_redis()


app = FastAPI(
    title="图片风格转换系统",
    description="基于AI的图片风格转换后端API，支持用户管理、会话管理和风格转换功能",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器内部错误: {str(exc)}",
            "data": None,
        },
    )


app.include_router(auth.router)
app.include_router(session.router)
app.include_router(style.router)
app.include_router(styles.router)

upload_path = os.path.abspath(settings.UPLOAD_DIR)
if os.path.isdir(upload_path):
    app.mount("/uploads", StaticFiles(directory=upload_path), name="uploads")

presets_path = str(PRESETS_DIR)
if PRESETS_DIR.is_dir():
    app.mount("/presets", StaticFiles(directory=presets_path), name="presets")


@app.get("/", tags=["健康检查"])
async def root():
    return {"message": "图片风格转换系统API正在运行", "version": "1.0.0"}


@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "healthy"}
