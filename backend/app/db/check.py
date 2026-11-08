import os
from pathlib import Path
from sqlalchemy import create_engine , text

Path("data").mkdir(exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
engine = create_engine( DATABASE_URL , connect_args={"check_same_thread":False})

def check_database():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))