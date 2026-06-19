import logging
import uuid

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    status,
    Depends,
    Header,
    Response,
)
from sqlalchemy.orm import Session
from google.genai import errors as genai_errors

from app.core.database import get_db
from app.contracts.models import Contract
from app.contracts.schemas import (
    ContractAnalysisResponse,
    ContractAnalysis,
    SavedContractSummary,
    SavedContractDetail,
)
from app.contracts.services import (
    extract_text_from_pdf,
    analyze_contract_with_ai,
    classify_contract_type,
)

logger = logging.getLogger("contracts")

router = APIRouter(prefix="/contracts", tags=["Contracts"])


def _to_summary(c: Contract) -> SavedContractSummary:
    analysis = c.analysis or {}
    return SavedContractSummary(
        id=c.id,
        filename=c.filename,
        size_bytes=c.size_bytes,
        detected_type=c.detected_type,
        contract_type=analysis.get("contract_type"),
        summary=analysis.get("summary"),
        created_at=c.created_at,
    )


@router.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    x_client_id: str = Header(default="anonymous"),
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un documento PDF.",
        )

    try:
        extracted_text = await extract_text_from_pdf(file)

        # Recuperamos los bytes del archivo (para tamaño y para guardarlo).
        await file.seek(0)
        content = await file.read()
        size_bytes = len(content)

        if not extracted_text.strip():
            return ContractAnalysisResponse(
                filename=file.filename,
                status="No se pudo extraer texto",
                message="El PDF no contiene texto seleccionable. Puede ser un escaneo de imagen.",
                size_bytes=size_bytes,
            )

        text_preview = (
            extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
        )

        # Paso 1: clasificacion previa con Gemma para gatear el analisis.
        detected = await classify_contract_type(extracted_text)

        if detected == "no_contrato":
            return ContractAnalysisResponse(
                filename=file.filename,
                status="No es un contrato",
                message="El documento subido no parece ser un contrato. Por ahora solo analizamos contratos de compraventa, trabajo o alquiler de inmueble.",
                extracted_text_preview=text_preview,
                size_bytes=size_bytes,
                detected_type=detected,
            )

        if detected == "otro_contrato":
            return ContractAnalysisResponse(
                filename=file.filename,
                status="Tipo no soportado",
                message="Detectamos que es un contrato, pero no de los tipos que soportamos por ahora (compraventa, trabajo o alquiler de inmueble).",
                extracted_text_preview=text_preview,
                size_bytes=size_bytes,
                detected_type=detected,
            )

        # Paso 2: si la clasificacion paso (o si no hay API key, detected=None),
        # continuamos con el analisis profundo, pasando el tipo para que inyecte
        # el marco legal y las clausulas esperadas del modelo correspondiente.
        analysis_data = await analyze_contract_with_ai(extracted_text, detected)

        if analysis_data is None:
            return ContractAnalysisResponse(
                filename=file.filename,
                status="Analizado parcialmente",
                message="Texto extraido correctamente. Configura GEMINI_API_KEY para habilitar el analisis con IA.",
                extracted_text_preview=text_preview,
                size_bytes=size_bytes,
                detected_type=detected,
            )

        analysis = ContractAnalysis(**analysis_data)

        # Guardado automatico (solo contratos analizados con exito). Resiliente:
        # si la DB falla, igual devolvemos el analisis al usuario.
        saved_id = None
        try:
            row = Contract(
                owner_id=x_client_id,
                filename=file.filename,
                size_bytes=size_bytes,
                detected_type=detected,
                pdf_data=content,
                analysis=analysis.model_dump(),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            saved_id = row.id
        except Exception as e:
            db.rollback()
            logger.warning("No se pudo guardar el contrato: %s", e)

        return ContractAnalysisResponse(
            filename=file.filename,
            status="Analizado",
            message="Analisis completado con exito.",
            extracted_text_preview=text_preview,
            size_bytes=size_bytes,
            detected_type=detected,
            analysis=analysis,
            id=saved_id,
        )

    except HTTPException:
        raise
    except genai_errors.ServerError:
        # La API de Gemini sigue caida tras los reintentos (5xx). No es un error
        # nuestro: devolvemos 503 para que el frontend sugiera reintentar.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de IA esta temporalmente sobrecargado. Volve a intentar en unos segundos.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el PDF: {str(e)}",
        )


@router.get("", response_model=list[SavedContractSummary])
def list_contracts(
    db: Session = Depends(get_db),
    x_client_id: str = Header(default="anonymous"),
):
    rows = (
        db.query(Contract)
        .filter(Contract.owner_id == x_client_id)
        .order_by(Contract.created_at.desc())
        .all()
    )
    return [_to_summary(c) for c in rows]


def _get_owned(contract_id: uuid.UUID, client_id: str, db: Session) -> Contract:
    row = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.owner_id == client_id)
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contrato no encontrado."
        )
    return row


@router.get("/{contract_id}", response_model=SavedContractDetail)
def get_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    x_client_id: str = Header(default="anonymous"),
):
    c = _get_owned(contract_id, x_client_id, db)
    summary = _to_summary(c)
    return SavedContractDetail(**summary.model_dump(), analysis=c.analysis)


@router.get("/{contract_id}/file")
def get_contract_file(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    x_client_id: str = Header(default="anonymous"),
):
    c = _get_owned(contract_id, x_client_id, db)
    return Response(
        content=bytes(c.pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{c.filename}"'},
    )


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    x_client_id: str = Header(default="anonymous"),
):
    c = _get_owned(contract_id, x_client_id, db)
    db.delete(c)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
