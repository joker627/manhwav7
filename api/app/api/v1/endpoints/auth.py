from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.service.auth import login_user
from app.schemas.auth import LoginResponse, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db=Depends(get_db)):
    token = login_user(db, credentials.email, credentials.password)
    return {
        "access_token": token,
        "token_type": "bearer"
    }
