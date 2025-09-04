from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, update
from typing import List, Optional, Tuple
from app.models import User, Application, ApplicationStatus
from app.models_apikeys import ApiKey

# ===== USER CRUD OPERATIONS =====
def create_user(db: Session, *, email: str, full_name: Optional[str]) -> User:
    """Create a new user in the database"""
    user = User(email=email, full_name=full_name)
    db.add(user)      # Add to session
    db.commit()       # Commit transaction to DB
    db.refresh(user)  # Refresh to get DB-generated values (like ID)
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email address"""
    return db.scalar(select(User).where(User.email == email))

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.get(User, user_id)

# ===== APPLICATION CRUD OPERATIONS =====
def create_application(
    db: Session,
    *,
    user_id: int,
    company: str,
    role_title: str,
    source: Optional[str],
    status: ApplicationStatus,
    job_url: Optional[str],
    notes: Optional[str]
) -> Application:
    """Create a new application in the database"""
    app = Application(
        user_id=user_id,
        company=company,
        role_title=role_title,
        source=source,
        status=status,
        job_url=job_url,
        notes=notes,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app

def list_applications(
    db: Session,
    *,
    user_id: Optional[int],
    status: Optional[ApplicationStatus],
    limit: int,
    offset: int
) -> Tuple[List[Application], int]:
    """List applications with filtering and pagination"""
    # Start with base query
    stmt = select(Application)
    
    # Apply filters if provided
    if user_id is not None:
        stmt = stmt.where(Application.user_id == user_id)
    if status is not None:
        stmt = stmt.where(Application.status == status)
    
    # Get total count (before pagination)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    
    # Apply ordering and pagination
    stmt = stmt.order_by(desc(Application.created_at)).limit(limit).offset(offset)
    
    # Execute query and return results
    rows = db.scalars(stmt).all()
    return rows, int(total or 0)

# ===== API KEY CRUD OPERATIONS =====
def create_api_key(
    db: Session, 
    *, 
    user_id: int, 
    name: str, 
    prefix: str, 
    secret_enc: str
) -> ApiKey:
    """Create a new API key for a user"""
    ak = ApiKey(
        user_id=user_id,
        name=name,
        prefix=prefix,
        secret_enc=secret_enc
    )
    db.add(ak)
    db.commit()
    db.refresh(ak)
    return ak

def deactivate_api_key(db: Session, *, key_id: int) -> None:
    """Deactivate an API key (soft delete)"""
    ak = db.get(ApiKey, key_id)
    if ak:
        ak.is_active = False
        db.commit()

def list_api_keys(db: Session, *, user_id: int) -> List[ApiKey]:
    """List all API keys for a user"""
    return db.scalars(
        select(ApiKey)
        .where(ApiKey.user_id == user_id)
        .order_by(ApiKey.created_at.desc())
    ).all()

def get_api_key_by_prefix(db: Session, *, prefix: str) -> Optional[ApiKey]:
    """Get API key by its prefix"""
    return db.scalar(
        select(ApiKey).where(
            ApiKey.prefix == prefix,
            ApiKey.is_active == True
        )
    )

def update_last_used(db: Session, *, key_id: int) -> None:
    """Update the last_used timestamp for an API key"""
    db.execute(
        update(ApiKey)
        .where(ApiKey.id == key_id)
        .values(last_used_at=func.now())
    )
    db.commit()