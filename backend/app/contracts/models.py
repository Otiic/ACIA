import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, LargeBinary, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Contract(Base):
    """Contrato analizado y persistido.

    Guarda el PDF original (bytea) y el analisis completo (JSONB) en la misma
    fila: la relacion contrato<->analisis es 1:1, asi que una sola tabla alcanza.
    Solo se guardan contratos analizados con exito (los rechazados no).
    """

    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Identificador anonimo del navegador (no hay login todavia).
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    size_bytes: Mapped[int] = mapped_column(Integer)
    detected_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pdf_data: Mapped[bytes] = mapped_column(LargeBinary)
    analysis: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
