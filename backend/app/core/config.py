from app.db.connection import make_engine
DATABASE_URL = "sqlite:///./data/study.db"
engine = make_engine(DATABASE_URL)
