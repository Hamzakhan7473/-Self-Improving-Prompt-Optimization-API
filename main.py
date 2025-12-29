"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from storage import init_db
from api import prompts, inference, evaluation, improvement, ab_testing


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application."""
    # Startup
    init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Self-Improving Prompt Optimization API",
    description="CI/CD for prompts with automated evaluation and self-improvement",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prompts.router)
app.include_router(inference.router)
app.include_router(evaluation.router)
app.include_router(improvement.router)
app.include_router(ab_testing.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Self-Improving Prompt Optimization API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug
    )

