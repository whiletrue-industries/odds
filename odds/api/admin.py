from fastapi import APIRouter, Depends, HTTPException
from .resolve_firebase_user import FireBaseUser

router = APIRouter(
    prefix="/admin",
)

@router.get("/")
async def read_items(user: FireBaseUser):
    return dict(user=user)

