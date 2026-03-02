from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.bootstrap import ensure_s3_bucket
from app.core.middleware import CorrelationIdMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.billing.router import router as billing_router
from app.modules.documents.router import router as documents_router
from app.modules.files.router import router as files_router
from app.modules.jobs.router import router as jobs_router
from app.modules.masterdata.router import router as masterdata_router
from app.modules.ocr.router import router as ocr_router
from app.modules.onboarding.router import router as onboarding_router
from app.modules.payroll.router import router as payroll_router
from app.modules.tasks.router import router as tasks_router
from app.modules.fleet.router import router as fleet_router
from app.modules.reports.router import router as reports_router
from app.modules.settings.router import router as settings_router
from app.modules.audit.router import router as audit_router
from app.modules.notifications.router import router as notifications_router
from app.modules.gdpr.router import router as gdpr_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        ensure_s3_bucket()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("S3 bucket init failed (will retry): %s", e)
    yield
    # Shutdown


app = FastAPI(
    title="SAF Logistic API",
    version="1.0.0",
    description="SaaS B2B pour entreprises de transport routier",
    lifespan=lifespan,
)

# Rate limiting with slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(CorrelationIdMiddleware)

# CORSMiddleware added LAST so it is outermost (handles preflight before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire all routers
app.include_router(auth_router)
app.include_router(files_router)
app.include_router(masterdata_router)
app.include_router(jobs_router)
app.include_router(documents_router)
app.include_router(billing_router)
app.include_router(payroll_router)
app.include_router(ocr_router)
app.include_router(tasks_router)
app.include_router(onboarding_router)
app.include_router(fleet_router)
app.include_router(reports_router)
app.include_router(settings_router)
app.include_router(audit_router)
app.include_router(notifications_router)
app.include_router(gdpr_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
