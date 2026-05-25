from __future__ import annotations

from dataclasses import asdict

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover - scaffold-friendly fallback
    class FastAPI:  # type: ignore[no-redef]
        def get(self, _path: str):
            def decorator(fn):
                return fn

            return decorator

from f1dashboard.services.dashboard import DashboardService

app = FastAPI()  # type: ignore[call-arg]
service = DashboardService()


@app.get("/api/dashboard")
def get_dashboard() -> dict:
    return asdict(service.get_snapshot())


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
