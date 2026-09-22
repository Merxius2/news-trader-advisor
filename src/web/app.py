"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config_loader import load_settings
from src.web.jobs import run_news_cycle
from src.web.routes import router
from src.scheduler import BackgroundSchedulerService

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = Jinja2Templates(directory=str(ROOT / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    scheduler = BackgroundSchedulerService(settings)

    def poll() -> None:
        run_news_cycle(settings, write_report=False)

    def hourly() -> None:
        run_news_cycle(settings, write_report=True)

    scheduler.add_jobs(poll_job=poll, hourly_job=hourly)
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    scheduler.stop()


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="Crypto News Advisor", lifespan=lifespan)
    app.state.settings = settings
    app.state.templates = TEMPLATES
    static_dir = ROOT / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.include_router(router)
    return app


app = create_app()
