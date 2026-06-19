from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import get_settings

settings = get_settings()

# Usar psycopg v3 en vez de psycopg2 (evita bugs de encoding en Windows español)
db_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+psycopg://"
)

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency para inyectar la sesion de BD en las rutas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

