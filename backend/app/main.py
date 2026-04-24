from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analysis, auth, documents, organizations, projects
from app.core.config import settings
from app.core.database import create_all_tables, get_db_context
from app.services import seed as seed_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_all_tables()
    with get_db_context() as db:
        seed_service.seed_demo(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(analysis.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
