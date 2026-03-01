from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.bootstrap import ensure_s3_bucket
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/health")
async def health():
    return {"status": "ok"}
