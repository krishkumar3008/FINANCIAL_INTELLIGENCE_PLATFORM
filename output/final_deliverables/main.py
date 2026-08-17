import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("api")

app = FastAPI(
    title="Nifty 100 Financial Intelligence Platform REST API",
    description="Production REST API providing access to Nifty 100 financial data, KPIs, screener, sector analysis, peer percentiles, and tearsheet PDFs.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware (allow all origins for internal use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000.0  # in ms
    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.2f}ms"
    )
    return response


# Include Routers with /api/v1 prefix
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(companies.router, prefix="/api/v1", tags=["Companies"])
app.include_router(screener.router, prefix="/api/v1", tags=["Screener"])
app.include_router(sectors.router, prefix="/api/v1", tags=["Sectors"])
app.include_router(peers.router, prefix="/api/v1", tags=["Peers"])
app.include_router(valuation.router, prefix="/api/v1", tags=["Valuation"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["Portfolio"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Nifty 100 Financial Intelligence Platform API v1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
