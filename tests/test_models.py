from sqlalchemy import inspect
from app.db import engine

def test_tables_exist():
    insp = inspect(engine)
    assert "users" in insp.get_table_names()
    assert "applications" in insp.get_table_names()