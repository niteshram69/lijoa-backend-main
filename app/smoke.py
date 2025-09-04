from sqlalchemy.orm import Session
from sqlalchemy import delete
from app.db import engine
from app.models import User, Application, ApplicationStatus
from datetime import datetime

with Session(engine) as s:
    # Clean up existing data
    s.execute(delete(Application))
    s.execute(delete(User))
    s.commit()
    
    # Now insert fresh data
    u = User(email="demo@lijoa.test", full_name="Demo User")
    s.add(u)
    s.flush()  # get u.id
    
    a = Application(
        user_id=u.id,
        company="OpenAI",
        role_title="ML Engineer",
        source="linkedin",
        status=ApplicationStatus.APPLIED,
        job_url="https://example.com/job",
        notes="First test",
        applied_at=datetime.utcnow(),
    )
    s.add(a)
    s.commit()
    
    print("Inserted:", {"user_id": u.id, "application_id": a.id})