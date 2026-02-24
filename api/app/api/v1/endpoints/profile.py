# app/api/v1/endpoints/profile.py
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.schemas.auth import ProfileResponse

router = APIRouter(tags=["perfil"])


@router.get("/profile", response_model=ProfileResponse)
def profile(user=Depends(get_current_user)):
    return user
