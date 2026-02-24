from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routes import api_router

app = FastAPI(
    title=settings.API_NAME,
    version=settings.API_VERSION,
    description="API para gestionar mangas, capítulos y usuarios en MangaVerse",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta raíz
@app.get("/", tags=["salud"])
def health():
    return {"message": "Welcome to the MangaVerse API!",
            "status":"funcional",
            "coment":"Actualmente esta en construcion puede haber errores"}

# API v1
app.include_router(api_router, prefix="/api/v1")


# uvicorn app.main:app --host 0.0.0.0 --port 8000
