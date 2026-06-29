# ACIA — Análisis de Contratos con IA

Proyecto para materia Ingenieria de Software.

Plataforma *LegalTech* que analiza contratos en PDF (**alquiler**, **compraventa** y **trabajo**)
y los explica en lenguaje claro, fundamentando cada hallazgo en la normativa argentina y
resaltándolo sobre el documento original.

> ⚠️ **Aviso:** herramienta de carácter informativo y orientativo. **No constituye
> asesoramiento legal** ni reemplaza la consulta con un profesional matriculado.

## ¿Qué hace?

- **Carga de PDF** y extracción de texto (PyMuPDF).
- **Clasificación automática** del tipo de contrato (Gemma 4 31B) como *gate*: rechaza lo que
  no es un contrato o no es de un tipo soportado.
- **Análisis estructurado** (Gemini 2.5 Flash) fundamentado en *checklists* legales destilados
  (CCyC y LCT) y en las cláusulas esperadas de cada modelo de contrato.
- **Visor de PDF** navegable con **resaltado interactivo**: cada cláusula u observación se
  marca sobre el texto original y muestra el detalle al pasar el mouse.
- **Persistencia**: los contratos analizados se guardan ("Mis contratos" e "Historial"),
  separados por navegador mediante un identificador anónimo.

## Stack

| Capa | Tecnologías |
|---|---|
| Backend | FastAPI · SQLAlchemy · PostgreSQL (psycopg) · PyMuPDF · google-genai (Gemini / Gemma) |
| Frontend | React 19 · Vite · react-pdf · axios · lucide-react |

## Puesta en marcha

### Requisitos
- Python 3.11+, Node 18+, PostgreSQL en ejecución, y una API key de Google AI Studio.

### Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash) — en Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

Creá un archivo `backend/.env` (no se versiona) con:
```env
PROJECT_NAME=ACA Legal AI Agent
DATABASE_URL=postgresql://USUARIO:CONTRASEÑA@localhost:5432/aca_db
GEMINI_API_KEY=tu_api_key
```

Levantá la API:
```bash
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

La app queda en `http://localhost:5173` y consume la API en `http://localhost:8000`.
