from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db import get_db
from app.schemas import ApplicationCreate, ApplicationsList, ApplicationOut, ApplicationStatus
from app import crud

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    # ensure user exists
    user = crud.get_user(db, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    app = crud.create_application(
        db,
        user_id=payload.user_id,
        company=payload.company.strip(),
        role_title=payload.role_title.strip(),
        source=(payload.source or None),
        status=payload.status,
        job_url=payload.job_url,
        notes=payload.notes,
    )
    return app

@router.get("", response_model=ApplicationsList)
def list_applications(
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(default=None),
    status: Optional[ApplicationStatus] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    items, total = crud.list_applications(db, user_id=user_id, status=status, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}