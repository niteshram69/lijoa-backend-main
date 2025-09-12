import hmac, hashlib, secrets, time
from typing import Optional, Tuple
from fastapi import Header, HTTPException, status, Request
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from app.config import settings
from app.models_apikeys import ApiKey
from app.models import User
from app.db import get_db
from sqlalchemy import select, update
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Depends
from datetime import datetime

# Initialize Fernet with secret (or generate if not provided)
FERNET = Fernet(
    settings.API_KEY_ENC_SECRET.encode() 
    if settings.API_KEY_ENC_SECRET 
    else Fernet.generate_key()
)

def make_api_key_pair() -> Tuple[str, str, str]:
    """Generate a new API key pair (prefix, secret, full token)"""
    prefix = secrets.token_urlsafe(8)[:12]  # Short ID shown/stored
    secret = secrets.token_urlsafe(32)     # Only shown once to client
    token = f"ak_{prefix}.{secret}"        # Full token for client
    return prefix, secret, token

def encrypt_secret(secret: str) -> str:
    """Encrypt the secret for storage"""
    return FERNET.encrypt(secret.encode()).decode()

def decrypt_secret(secret_enc: str) -> str:
    """Decrypt the secret from storage"""
    return FERNET.decrypt(secret_enc.encode()).decode()

async def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Tuple[User, ApiKey, str]:
    """
    Dependency to authenticate requests using API key.
    Returns (User, ApiKey, secret) tuple.
    """
    if not x_api_key or not x_api_key.startswith("ak_") or "." not in x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key"
        )
    
    try:
        _, rest = x_api_key.split("ak_", 1)
        prefix, provided_secret = rest.split(".", 1)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    # Find API key by prefix
    ak = db.scalar(
        select(ApiKey).where(
            ApiKey.prefix == prefix, 
            ApiKey.is_active == True
        )
    )
    
    if not ak:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key not found"
        )
    
    # Verify secret
    real_secret = decrypt_secret(ak.secret_enc)
    if not hmac.compare_digest(real_secret, provided_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key mismatch"
        )
    
    # Get user
    user = db.get(User, ak.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for API key"
        )
    
    # Update last used timestamp
    db.execute(
        update(ApiKey)
        .where(ApiKey.id == ak.id)
        .values(last_used_at=datetime.utcnow())
    )
    db.commit()
    
    return user, ak, real_secret

async def verify_signature_if_present(
    request: Request,
    api: Tuple[User, ApiKey, str] = Depends(require_api_key),
    x_timestamp: Optional[str] = Header(default=None, alias="X-Timestamp"),
    x_signature: Optional[str] = Header(default=None, alias="X-Signature"),
):
    """
    Optional HMAC signature verification.
    Clients may send:
    - X-Timestamp: Unix seconds
    - X-Signature: hex(HMAC_SHA256(secret, f"{method}\n{path}\n{timestamp}\n{body}"))
    """
    user, ak, secret = api
    
    # Skip if no signature headers
    if not x_signature and not x_timestamp:
        return
    
    # Validate timestamp
    try:
        ts = int(x_timestamp or "0")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Timestamp"
        )
    
    # Check for stale requests (5 minutes tolerance)
    if abs(int(time.time()) - ts) > 300:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Stale request"
        )
    
    # Verify signature
    body_bytes = await request.body()
    to_sign = f"{request.method}\n{request.url.path}\n{ts}\n".encode() + body_bytes
    expected = hmac.new(
        secret.encode(), 
        to_sign, 
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected, (x_signature or "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad signature"
        )

class SignatureCaptureMiddleware(BaseHTTPMiddleware):
    """Middleware for capturing signatures (placeholder for future use)"""
    async def dispatch(self, request: Request, call_next):
        # No-op placeholder; kept for future logging/body replay handling
        response = await call_next(request)
        return response