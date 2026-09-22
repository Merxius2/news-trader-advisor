"""Dashboard HTTP routes."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from src.config_loader import load_settings, load_watchlist
from src.storage.db import db_session, init_db
from src.web.bot_state import set_bot_enabled
from src.web.jobs import trigger_news_cycle_async
from src.web.queries import (
    fetch_activity_log,
    fetch_suggestions,
    fetch_watchlist_signals,
    list_digest_files,
    system_status,
)

router = APIRouter()
ROOT = Path(__file__).resolve().parents[2]


def _templates(request: Request):
    return request.app.state.templates


def _settings(request: Request):
    return request.app.state.settings


def _conn_ctx(settings):
    db_path = init_db(Path(settings.database.path))
    return db_session(db_path)


@router.get("/dashboard.html")
def dashboard_html_redirect():
    return RedirectResponse("/", status_code=302)


@router.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request):
    settings = _settings(request)
    watchlist = load_watchlist()
    with _conn_ctx(settings) as conn:
        ctx = {
            "page_title": "Dashboard",
            "active_nav": "dashboard",
            "status": system_status(conn, settings),
            "watchlist": fetch_watchlist_signals(conn, watchlist),
            "suggestions": fetch_suggestions(conn, limit=8),
            "activity": fetch_activity_log(conn, limit=30),
            "activity_filter": "all",
            "now_str": datetime.now().strftime("%A %d %b %Y · %H:%M"),
        }
    return _templates(request).TemplateResponse(request, "dashboard.html", ctx)


@router.get("/suggestions", response_class=HTMLResponse)
def suggestions_page(request: Request):
    settings = _settings(request)
    with _conn_ctx(settings) as conn:
        ctx = {
            "page_title": "Suggestions",
            "active_nav": "suggestions",
            "status": system_status(conn, settings),
            "suggestions": fetch_suggestions(conn, limit=50),
        }
    return _templates(request).TemplateResponse(request, "suggestions.html", ctx)


@router.get("/watchlist", response_class=HTMLResponse)
def watchlist_page(request: Request):
    settings = _settings(request)
    watchlist = load_watchlist()
    with _conn_ctx(settings) as conn:
        ctx = {
            "page_title": "Watchlist",
            "active_nav": "watchlist",
            "status": system_status(conn, settings),
            "watchlist": fetch_watchlist_signals(conn, watchlist),
        }
    return _templates(request).TemplateResponse(request, "watchlist.html", ctx)


@router.get("/activity", response_class=HTMLResponse)
def activity_log_page(request: Request, filter: str = "all"):
    settings = _settings(request)
    with _conn_ctx(settings) as conn:
        ctx = {
            "page_title": "Activity log",
            "active_nav": "activity",
            "status": system_status(conn, settings),
            "activity": fetch_activity_log(conn, event_type=filter, limit=100),
            "activity_filter": filter,
        }
    return _templates(request).TemplateResponse(request, "activity.html", ctx)


@router.get("/digests", response_class=HTMLResponse)
def digests_page(request: Request):
    settings = _settings(request)
    reports_dir = ROOT / "reports"
    with _conn_ctx(settings) as conn:
        ctx = {
            "page_title": "Digests",
            "active_nav": "digests",
            "status": system_status(conn, settings),
            "digests": list_digest_files(reports_dir),
        }
    return _templates(request).TemplateResponse(request, "digests.html", ctx)


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    settings = _settings(request)
    with _conn_ctx(settings) as conn:
        ctx = {
            "page_title": "Settings",
            "active_nav": "settings",
            "status": system_status(conn, settings),
            "settings": settings,
        }
    return _templates(request).TemplateResponse(request, "settings.html", ctx)


@router.get("/activity/feed", response_class=HTMLResponse)
def activity_feed_partial(request: Request, filter: str = "all"):
    settings = _settings(request)
    with _conn_ctx(settings) as conn:
        activity = fetch_activity_log(conn, event_type=filter, limit=30)
    return _templates(request).TemplateResponse(
        request,
        "partials/activity_feed.html",
        {"activity": activity, "activity_filter": filter},
    )


@router.get("/partials/suggestions", response_class=HTMLResponse)
def suggestions_partial(request: Request):
    settings = _settings(request)
    with _conn_ctx(settings) as conn:
        suggestions = fetch_suggestions(conn, limit=8)
    return _templates(request).TemplateResponse(
        request,
        "partials/suggestions_list.html",
        {"suggestions": suggestions},
    )


@router.get("/partials/bot-status", response_class=HTMLResponse)
def bot_status_partial(request: Request):
    settings = _settings(request)
    with _conn_ctx(settings) as conn:
        status = system_status(conn, settings)
    return _templates(request).TemplateResponse(
        request,
        "partials/bot_status.html",
        {"status": status},
    )


@router.post("/actions/run-news")
def trigger_news_run(request: Request):
    settings = _settings(request)
    started = trigger_news_cycle_async(settings)
    if request.headers.get("HX-Request"):
        with _conn_ctx(settings) as conn:
            status = system_status(conn, settings)
        return _templates(request).TemplateResponse(
            request,
            "partials/bot_status.html",
            {"status": status},
            headers={"HX-Trigger": "refreshActivity,refreshSuggestions"},
        )
    return JSONResponse({"started": started})


@router.post("/actions/bot-toggle")
def bot_toggle(request: Request, enabled: str = Form(...)):
    settings = _settings(request)
    on = enabled.lower() in ("1", "true", "on", "yes")
    with _conn_ctx(settings) as conn:
        set_bot_enabled(conn, on)
        status = system_status(conn, settings)
    if request.headers.get("HX-Request"):
        return _templates(request).TemplateResponse(
            "partials/bot_status.html",
            {"request": request, "status": status},
        )
    return RedirectResponse("/", status_code=303)


@router.get("/api/health")
def health_check():
    return {"status": "ok"}


@router.get("/api/status")
def system_status_api(request: Request):
    settings = _settings(request)
    with _conn_ctx(settings) as conn:
        return system_status(conn, settings)
