import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator
from typing import Optional, List


class KeyClause(BaseModel):
    title: str
    description: str
    # Cita textual EXACTA del contrato que sustenta esta clausula (para resaltar
    # en el PDF). Puede venir vacia si la IA no encontro una frase literal.
    quote: str = ""


class Concern(BaseModel):
    text: str
    quote: str = ""

    @field_validator("text", mode="before")
    @classmethod
    def _coerce_plain_string(cls, v):
        # Robustez: si la IA devuelve la observacion como string suelto en vez
        # de objeto, igual lo aceptamos.
        return v


class ContractAnalysis(BaseModel):
    summary: str
    contract_type: str
    parties: List[str]
    key_clauses: List[KeyClause]
    potential_concerns: List[Concern]

    @field_validator("potential_concerns", mode="before")
    @classmethod
    def _normalize_concerns(cls, items):
        # Acepta tanto ["texto", ...] (formato viejo) como [{"text":...,"quote":...}].
        if not isinstance(items, list):
            return items
        normalized = []
        for it in items:
            if isinstance(it, str):
                normalized.append({"text": it, "quote": ""})
            else:
                normalized.append(it)
        return normalized


class ContractAnalysisResponse(BaseModel):
    filename: str
    status: str
    message: str
    extracted_text_preview: Optional[str] = None
    size_bytes: int
    detected_type: Optional[str] = None
    analysis: Optional[ContractAnalysis] = None
    # id del contrato guardado (presente solo si el analisis se persistio).
    id: Optional[uuid.UUID] = None


class SavedContractSummary(BaseModel):
    """Item de lista para 'Mis contratos' / 'Historial' (sin el PDF)."""

    id: uuid.UUID
    filename: str
    size_bytes: int
    detected_type: Optional[str] = None
    contract_type: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime


class SavedContractDetail(SavedContractSummary):
    """Detalle de un contrato guardado, con el analisis completo."""

    analysis: ContractAnalysis
