from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Safety-first weather decision copilot backend for SIH26068.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "message": "WeatherGPT backend is running.",
        "docs": "/docs",
        "design_rule": "LLM/language layer explains structured weather data; it is not the meteorological source of truth.",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.app_env}


app.include_router(router, prefix=settings.api_prefix)
