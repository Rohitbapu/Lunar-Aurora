import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.entities import Base

# Try PostGIS first if configured and accessible, otherwise fallback gracefully to SQLite
engine = None
USE_POSTGIS = False

if os.getenv("ENABLE_POSTGRES") == "1":
    try:
        engine = create_engine(settings.POSTGIS_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            pass
        USE_POSTGIS = True
        print("[Database] Successfully connected to PostGIS database.")
    except Exception as e:
        print(f"[Database] PostGIS connection failed: {e}. Falling back to SQLite.")

if engine is None:
    connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
    print(f"[Database] Connected to default database: {settings.DATABASE_URL}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

