import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db, engine, Base
from app.core.config import get_settings
from app.contracts import models  # noqa: F401  registra el modelo en Base.metadata
from app.contracts.routers import router as contracts_router

settings = get_settings()

# Crea las tablas si no existen. Lo envolvemos en try/except para que la app
# arranque igual aunque Postgres no este disponible (el analisis sigue andando;
# solo el guardado fallara, manejado de forma graciosa en el router).
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.getLogger("contracts").warning(
        "No se pudieron crear/verificar las tablas en el arranque: %s", e
    )

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contracts_router)

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a ACA Legal AI Agent API!"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Prueba simple de conexion a la base de datos
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "online",
        "database": db_status
    }
