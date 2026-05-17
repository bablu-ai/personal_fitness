import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from dotenv import load_dotenv
from alembic.config import Config
from alembic import command
from app.routers import upload, todos, dashboard, benefits, agent, rotation, screenings

load_dotenv(override=True)  # .env values take precedence over system env vars


def _run_migrations() -> None:
    """Apply any pending Alembic migrations on startup — safe to run repeatedly."""
    alembic_cfg = Config(Path(__file__).parent.parent / "alembic.ini")
    alembic_cfg.set_main_option("script_location", str(Path(__file__).parent.parent / "alembic"))
    command.upgrade(alembic_cfg, "head")

# Disable built-in docs so we can serve Swagger UI from local static files
# (avoids CDN dependency on cdn.jsdelivr.net which may be blocked on some networks)
_run_migrations()

app = FastAPI(
    title="Longevity Daily-Action API",
    version="0.1.0",
    description="Phase 1 POC — open architecture longevity app backend",
    docs_url=None,
    redoc_url=None,
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve swagger-ui static files from local directory
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/docs", include_in_schema=False)
async def swagger_ui():
    if STATIC_DIR.exists():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Longevity Daily API — Swagger UI",
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )
    # Fallback to CDN if static files not yet copied
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Longevity Daily API — Swagger UI",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_ui():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Longevity Daily API — ReDoc",
    )


app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(todos.router, prefix="/api", tags=["todos"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(benefits.router, prefix="/api", tags=["benefits"])
app.include_router(agent.router, prefix="/api", tags=["agent"])
app.include_router(rotation.router, prefix="/api", tags=["rotation"])
app.include_router(screenings.router, prefix="/api", tags=["screenings"])


@app.get("/api/health")
def health():
    return {"status": "ok", "phase": "1-poc"}
