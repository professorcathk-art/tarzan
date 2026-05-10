"""Tarzan FastAPI entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from config import get_settings

from db.models import Base

from db.session import engine

from engine.scheduling import shutdown_scheduler

from engine.scheduling import start_scheduler_if_enabled

from routers import backtest as backtest_router

from routers import schedules as schedules_router

from routers import screen as screen_router

from routers import strategies as strategies_router

from routers import templates as templates_router

from routers import universe as universe_router

from routers import webhooks as webhooks_router


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    sched = start_scheduler_if_enabled(settings.database_url)
    app.state.scheduler = sched
    yield
    shutdown_scheduler()


app = FastAPI(title="Tarzan Screener API", lifespan=lifespan)

settings = get_settings()


app.add_middleware(
    CORSMiddleware,

    allow_origins=settings.cors_origin_list or ["http://localhost:3000"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


@app.get("/health")

def health():
    return {"status": "ok", "scheduler": getattr(app.state, "scheduler") is not None}


app.include_router(screen_router.router, prefix="/api")
app.include_router(backtest_router.router, prefix="/api")
app.include_router(templates_router.router, prefix="/api")
app.include_router(schedules_router.router, prefix="/api")
app.include_router(strategies_router.router, prefix="/api")
app.include_router(universe_router.router, prefix="/api")


app.include_router(webhooks_router.router, prefix="/api")
