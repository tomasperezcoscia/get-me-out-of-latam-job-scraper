"""User profile API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import ProfileOut
from app.database import get_db
from app.models import UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db)) -> UserProfile:
    """Get the user profile."""
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
