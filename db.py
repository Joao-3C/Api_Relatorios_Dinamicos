import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("DB_USER", "JC")
PASS = os.getenv("DB_PASS", "SenhaForte!")
HOST = os.getenv("DB_HOST", "localhost")
PORT = os.getenv("DB_PORT", "1521")
SERVICE = os.getenv("DB_SERVICE", "XEPDB1")

# oracle+oracledb usa modo THIN por padrão (não precisa Instant Client)
DATABASE_URL = f"oracle+oracledb://{USER}:{PASS}@{HOST}:{PORT}/?service_name={SERVICE}"

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass

# Dependência do FastAPI
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
