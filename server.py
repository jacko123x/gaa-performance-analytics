"""ASGI deployment entry point with liveness and readiness routes."""

from pathlib import Path

import streamlit as st
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from starlette.routing import Route

from src.health import check_database_readiness


APP_SCRIPT = Path(__file__).resolve().parent / "dashboard" / "app.py"


async def health_endpoint(request):
    return JSONResponse({"status": "ok"})


async def readiness_endpoint(request):
    report = await run_in_threadpool(check_database_readiness)
    return JSONResponse(
        report.as_dict(),
        status_code=200 if report.ready else 503,
    )


app = st.App(
    str(APP_SCRIPT),
    routes=[
        Route("/api/health", health_endpoint),
        Route("/api/ready", readiness_endpoint),
    ],
)
