"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data import init_default_thrusters
from app.routers import compute, health, launch_options, thrusters


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    init_default_thrusters()
    yield
    # Shutdown (nothing to clean up for in-memory storage)


app = FastAPI(
    title="Satellite Propellant Budget Calculator",
    description="Calculate propellant requirements for satellite mission maneuvers",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(launch_options.router, prefix="/api")
app.include_router(thrusters.router, prefix="/api")
app.include_router(compute.router, prefix="/api")
