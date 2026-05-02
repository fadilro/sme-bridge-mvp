from fastapi import FastAPI
from app.api.routes import router as api_router

def create_app() -> FastAPI:
    """
    Application factory for the FastAPI backend.
    """
    app = FastAPI(
        title="SME Bridge MVP API",
        description="API for extracting Scope 3 data from utility bills.",
        version="0.1.0"
    )

    app.include_router(api_router)

    return app

app = create_app()
