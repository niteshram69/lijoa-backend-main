from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import ApiKeyCreate, ApiKeyOut, ApiKeyWithToken
from app import crud
from app.auth import make_api_key_pair, encrypt_secret
from app.models import User

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

@router.post("", response_model=ApiKeyWithToken, status_code=status.HTTP_201_CREATED)
def create_api_key(payload: ApiKeyCreate, db: Session = Depends(get_db)):
    """
    Create a new API key for a user.
    The token is only returned once - save it securely!
    """
    # Verify user exists
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate new key pair
    prefix, secret, token = make_api_key_pair()
    
    # Store encrypted secret
    ak = crud.create_api_key(
        db,
        user_id=payload.user_id,
        name=payload.name,
        prefix=prefix,
        secret_enc=encrypt_secret(secret)
    )
    
    # Return token ONCE
    return {
        "id": ak.id,
        "user_id": ak.user_id,
        "name": ak.name,
        "prefix": ak.prefix,
        "is_active": ak.is_active,
        "created_at": ak.created_at,
        "last_used_at": ak.last_used_at,
        "token": token,
    }

@router.get("/{user_id}", response_model=list[ApiKeyOut])
def list_keys(user_id: int, db: Session = Depends(get_db)):
    """List all API keys for a user (without secrets)"""
    return crud.list_api_keys(db, user_id=user_id)

@router.delete("/{key_id}", status_code=204)
def revoke_key(key_id: int, db: Session = Depends(get_db)):
    """Revoke (deactivate) an API key"""
    crud.deactivate_api_key(db, key_id=key_id)
    return