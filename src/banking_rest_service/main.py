from __future__ import annotations

from fastapi import FastAPI

from banking_rest_service.api.v1 import auth as auth_routes

app = FastAPI(
    title="Banking REST Service",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Simple health endpoint to verify the service is running."""
    return {"status": "ok"}


# Routers
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
