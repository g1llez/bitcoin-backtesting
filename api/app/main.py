from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import time
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional
import os

from .database import get_db, engine
from .services.db_bootstrap import run_startup_migrations
from .services.metrics import REQUEST_COUNT, REQUEST_LATENCY
from .models import models
from .routes import machines, efficiency, bitcoin_prices, fpps_data, backtest, market_data, sites, config, machine_templates

# Création des tables
models.Base.metadata.create_all(bind=engine)
# Migrations de démarrage (idempotentes)
run_startup_migrations(engine)

app = FastAPI(
    title="Bitcoin Backtesting API",
    description="API pour le backtesting de machines Bitcoin avec optimisation des ratios d'efficacité",
    version="1.0.0"
)
# Prometheus endpoint
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST  # type: ignore

@app.get("/metrics")
def metrics():
    data = generate_latest()
    from fastapi import Response
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# Configuration CORS (pilotée par variables d'environnement)
raw_origins = os.getenv("ALLOW_ORIGINS", "http://localhost:3001")
allow_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(machines.router, prefix="/api/v1", tags=["machines"])
app.include_router(efficiency.router, prefix="/api/v1", tags=["efficiency"])
app.include_router(bitcoin_prices.router, prefix="/api/v1", tags=["bitcoin-prices"])
app.include_router(fpps_data.router, prefix="/api/v1", tags=["fpps-data"])
app.include_router(backtest.router, prefix="/api/v1", tags=["backtest"])
app.include_router(market_data.router, prefix="/api/v1", tags=["market"])
app.include_router(sites.router, prefix="/api/v1", tags=["sites"])
app.include_router(config.router, prefix="/api/v1", tags=["config"])
app.include_router(machine_templates.router, prefix="/api/v1", tags=["machine-templates"])

@app.get("/")
async def root():
    """Point d'entrée principal de l'API"""
    return {
        "message": "Bitcoin Backtesting API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }

# Middleware simple pour métriques
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    path = request.url.path
    method = request.method
    try:
        REQUEST_COUNT.labels(method=method, path=path, status=response.status_code).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
    except Exception:
        pass
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 