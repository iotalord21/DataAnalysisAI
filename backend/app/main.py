from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.datasets import router as datasets_router
from app.api.analysis import router as analysis_router

app = FastAPI(
    title="Data Analysis Agent API",
    description="Autonomous Agentic Data Analysis system powered by LangGraph, FastAPI, and Python Sandbox.",
    version="1.0.0",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(datasets_router)
app.include_router(analysis_router)


@app.get("/health")
def healthcheck():
    return {
        "status": "healthy",
        "env": settings.app_env,
        "provider": settings.llm_provider,
        "model": settings.gemini_model if settings.llm_provider == "gemini" else settings.openai_model,
    }


@app.get("/api/info")
def system_info():
    has_gemini = bool(settings.gemini_api_key)
    has_openai = bool(settings.openai_api_key)
    has_anthropic = bool(settings.anthropic_api_key)

    return {
        "provider": settings.llm_provider,
        "providers_available": {
            "gemini": {"configured": has_gemini, "model": settings.gemini_model},
            "openai": {"configured": has_openai, "model": settings.openai_model},
            "anthropic": {"configured": has_anthropic, "model": settings.anthropic_model},
            "ollama": {"configured": True, "model": settings.ollama_model, "url": settings.ollama_base_url},
        },
        "sandbox": {
            "timeout_seconds": settings.execution_timeout_seconds,
            "max_retries": settings.max_verification_retries,
        }
    }
