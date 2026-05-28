import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import structlog
from app.api.v1.api import api_router
from app.core.config.settings import settings
from app.core.logging.structlog_config import configure_logging, set_correlation_id, set_trace_id

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting Call Quality Control AI API Service")
    yield
    logger.info("Shutting down Call Quality Control AI API Service")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_trace_headers(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))

    set_correlation_id(correlation_id)
    set_trace_id(trace_id)

    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Trace-ID"] = trace_id

    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_sec=round(duration, 4)
    )

    return response

app.include_router(api_router, prefix="/api/v1")
