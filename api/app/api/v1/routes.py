# app/api/v1/routes.py
from fastapi import APIRouter
from app.api.v1.endpoints import auth, profile, manga, economy

api_router = APIRouter()

api_router.include_router(auth.router)

api_router.include_router(profile.router)

api_router.include_router(manga.router, prefix="/manga", tags=["manga"])
api_router.include_router(economy.router)
