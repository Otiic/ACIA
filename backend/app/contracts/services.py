import asyncio
import json
import logging

import fitz  # PyMuPDF
from fastapi import UploadFile
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from app.core.config import get_settings
from app.contracts.knowledge import build_reference_block

settings = get_settings()

# Logger propio con handler garantizado, para que los mensajes de confirmacion
# aparezcan en consola sin depender de la config de logging de uvicorn.
logger = logging.getLogger("contracts")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

# Cliente unico del SDK nuevo google-genai.
# Reemplaza al deprecado google.generativeai, que no decodifica bien las
# respuestas de modelos "thinking" como Gemma 4 (devuelve texto basura y
# usage_metadata roto).
_client: genai.Client | None = None


def _get_client() -> genai.Client | None:
    global _client
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "placeholder":
        return None
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


# Los modelos preview de Gemini devuelven 5xx transitorios (500 INTERNAL,
# 503 high demand) bajo carga. Reintentamos con backoff exponencial.
_MAX_RETRIES = 4
_RETRY_BASE_DELAY = 1.0  # segundos


async def _generate_with_retry(client: genai.Client, **kwargs):
    """Llama a generate_content reintentando ante errores 5xx transitorios.

    Reintenta solo en ServerError (5xx). Los ClientError (4xx) se propagan
    directamente porque reintentar no los va a resolver.
    """
    delay = _RETRY_BASE_DELAY
    for attempt in range(_MAX_RETRIES):
        try:
            return await client.aio.models.generate_content(**kwargs)
        except genai_errors.ServerError:
            if attempt == _MAX_RETRIES - 1:
                raise
            await asyncio.sleep(delay)
            delay *= 2


# ============= ANALISIS PROFUNDO (Gemini) =============

# Limite de caracteres del contrato que mandamos al modelo.
MAX_CONTRACT_CHARS = 60_000

# Usamos un modelo GA (estable) y no preview. Los preview y los "lite" sufren
# 5xx por alta demanda; gemini-2.5-flash es GA, soporta JSON mode y es confiable.
ANALYSIS_MODEL = "gemini-2.5-flash"

ANALYSIS_PROMPT = """Sos un asistente legal experto en analisis de contratos. Te paso el texto
de un contrato y necesito que devuelvas un analisis estructurado en JSON.

{reference_block}

Respeta exactamente este esquema:
{{
  "summary": "Resumen breve del contrato en 2 o 3 oraciones, en español claro.",
  "contract_type": "Tipo de contrato (ej: 'Locacion de servicios', 'Compraventa', etc.).",
  "parties": ["Nombre de la parte 1", "Nombre de la parte 2"],
  "key_clauses": [
    {{
      "title": "Titulo corto de la clausula",
      "description": "Explicacion en lenguaje llano de que dice esa clausula.",
      "quote": "Fragmento textual EXACTO del contrato en el que se basa esta clausula."
    }}
  ],
  "potential_concerns": [
    {{
      "text": "Punto de atencion u observacion para revisar (en español).",
      "quote": "Fragmento textual EXACTO del contrato relacionado con esta observacion (vacio si no aplica)."
    }}
  ]
}}

Reglas:
- Devolve solo el JSON, sin texto adicional ni markdown.
- Si algun dato no esta en el contrato, usa el string "No especificado".
- Listas vacias estan permitidas si no hay informacion relevante.
- key_clauses debe tener entre 3 y 7 elementos cuando sea posible.
- potential_concerns puede ser vacio si no detectas riesgos relevantes.

MUY IMPORTANTE sobre "quote":
- "quote" debe ser una copia TEXTUAL y EXACTA de una frase que aparece en el TEXTO DEL CONTRATO de abajo (mismas palabras, mismos acentos, misma puntuacion). NO lo parafrasees ni lo inventes.
- Que sea una frase breve y especifica (idealmente entre 15 y 200 caracteres), suficiente para ubicarla en el documento.
- Si una observacion no corresponde a ninguna frase literal (ej. "Falta clausula: ..."), deja "quote" como string vacio "".

Si te di MATERIAL DE REFERENCIA arriba, usalo asi:
- Contrasta las clausulas del contrato contra el MARCO LEGAL y marca en potential_concerns toda clausula que sea nula, abusiva o contraria a la ley (citando el articulo cuando puedas).
- Compara el contrato contra las CLAUSULAS ESPERADAS del modelo y, si falta alguna importante, agregala en potential_concerns con el prefijo "Falta clausula:" y quote vacio.

TEXTO DEL CONTRATO:
\"\"\"
{contract_text}
\"\"\"
"""


# ============= CLASIFICACION PREVIA (Gemma) =============

# Tipos soportados para analisis profundo.
SUPPORTED_TYPES = {"compraventa", "trabajo", "alquiler"}
ALL_TYPES = SUPPORTED_TYPES | {"otro_contrato", "no_contrato"}

CLASSIFIER_MODEL = "gemma-4-31b-it"
CLASSIFIER_MAX_CHARS = 6_000

# IMPORTANTE: Gemma 4 es un "thinking model". Gasta tokens internos razonando
# antes de responder. Si max_output_tokens es chico (<200), no le queda
# presupuesto para escribir la respuesta y devuelve None.
CLASSIFIER_MAX_TOKENS = 512

CLASSIFIER_SYSTEM = (
    "Sos un clasificador automatico. Tu UNICA respuesta valida es una de estas 5 "
    "palabras exactas, en minusculas, sin nada mas (ni explicacion, ni markdown, "
    "ni puntuacion): compraventa, trabajo, alquiler, otro_contrato, no_contrato."
)

CLASSIFIER_PROMPT = """Clasifica este contrato. Responde solo una palabra: compraventa, trabajo, alquiler, otro_contrato o no_contrato.

CONTRATO:
{document_text}

TIPO:"""


# ============= FUNCIONES PUBLICAS =============


async def extract_text_from_pdf(file: UploadFile) -> str:
    """Extrae el texto de un archivo PDF usando PyMuPDF."""
    content = await file.read()
    pdf_document = fitz.open(stream=content, filetype="pdf")
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text


async def analyze_contract_with_ai(text: str, contract_type: str | None = None) -> dict | None:
    """Llama a Gemini para obtener un analisis estructurado del contrato.

    Si contract_type es uno de los soportados, inyecta el marco legal y las
    clausulas esperadas del modelo para fundamentar el analisis (ver knowledge.py).

    Devuelve un dict con la forma definida en el schema ContractAnalysis,
    o None si la API key no esta configurada o si la respuesta no es valida.
    """
    client = _get_client()
    if client is None:
        return None

    truncated_text = text[:MAX_CONTRACT_CHARS]
    reference_block = build_reference_block(contract_type) or ""

    # Log de confirmacion: deja claro en consola si el analisis se apoya en la
    # ley + modelo de referencia, y cuanto pesa ese material.
    if reference_block:
        logger.info(
            "[analisis] tipo=%s -> SI usa referencia (ley + modelo): %d chars (~%d tokens)",
            contract_type,
            len(reference_block),
            len(reference_block) // 4,
        )
    else:
        logger.info(
            "[analisis] tipo=%s -> SIN referencia (no hay material para este tipo)",
            contract_type,
        )

    prompt = ANALYSIS_PROMPT.format(
        contract_text=truncated_text,
        reference_block=reference_block,
    )

    response = await _generate_with_retry(
        client,
        model=ANALYSIS_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    if not response.text:
        return None

    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, ValueError):
        return None


async def classify_contract_type(text: str) -> str | None:
    """Clasifica el documento usando Gemma 4 31B.

    Devuelve uno de: compraventa | trabajo | alquiler | otro_contrato | no_contrato.
    Devuelve None si la API key no esta configurada.
    """
    client = _get_client()
    if client is None:
        return None

    truncated = text[:CLASSIFIER_MAX_CHARS]
    prompt = CLASSIFIER_PROMPT.format(document_text=truncated)

    response = await _generate_with_retry(
        client,
        model=CLASSIFIER_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=CLASSIFIER_SYSTEM,
            temperature=0.0,
            max_output_tokens=CLASSIFIER_MAX_TOKENS,
        ),
    )

    raw = (response.text or "").strip().lower()
    if not raw:
        return "otro_contrato"

    # Limpieza: sacar markdown y puntuacion del inicio/final.
    cleaned = raw.lstrip("*_`#> -").strip(".,;:!?\"'`* \n\t")

    first_token = cleaned.split()[0].strip(".,;:!?\"'`*") if cleaned else ""
    if first_token in ALL_TYPES:
        return first_token

    # Fallback por contenido. Orden: especificos primero para evitar
    # falsos positivos (ej. "no_contrato" contiene "contrato").
    for t in ("no_contrato", "otro_contrato", "compraventa", "trabajo", "alquiler"):
        if t in raw:
            return t

    return "otro_contrato"
