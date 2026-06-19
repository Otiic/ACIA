import {
  FileText,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Users,
  FileSignature,
  ArrowLeft,
} from 'lucide-react'
import PdfViewer from './PdfViewer'
import Disclaimer from './Disclaimer'
import { formatBytes, TYPE_LABELS } from '../lib/format'
import './UploadView.css'

/**
 * Vista de analisis (PDF + panel) reutilizable: la usa UploadView tras analizar
 * y tambien las vistas de "Mis contratos" / "Historial" al abrir uno guardado.
 *
 * Props:
 *  - result: { filename, size_bytes, detected_type, status, message, analysis }
 *  - file:   Blob/File del PDF (puede ser null si no esta disponible)
 *  - onBack: callback del boton volver
 *  - backLabel: texto del boton volver
 */
export default function AnalysisWorkspace({ result, file, onBack, backLabel = 'Volver' }) {
  const isRejection =
    result.status === 'No es un contrato' || result.status === 'Tipo no soportado'
  const HeadIcon = result.analysis
    ? CheckCircle2
    : isRejection
      ? AlertTriangle
      : AlertCircle

  // Highlights para el PDF: una entrada por cada clausula/observacion con cita.
  const analysis = result.analysis
  const highlights = []
  if (analysis) {
    analysis.key_clauses?.forEach((c, i) => {
      if (c.quote?.trim()) {
        highlights.push({
          id: `clause-${i}`,
          type: 'clause',
          quote: c.quote,
          label: c.title,
          text: c.description,
        })
      }
    })
    analysis.potential_concerns?.forEach((c, i) => {
      if (c.quote?.trim()) {
        highlights.push({
          id: `concern-${i}`,
          type: 'concern',
          quote: c.quote,
          label: 'Punto a revisar',
          text: c.text,
        })
      }
    })
  }

  return (
    <div className="upload-view upload-view--workspace">
      <header className="workspace__topbar">
        <button className="workspace__back" onClick={onBack}>
          <ArrowLeft size={14} strokeWidth={1.5} />
          <span>{backLabel}</span>
        </button>
        <div className="workspace__file">
          <FileText size={16} strokeWidth={1.5} />
          <div className="workspace__file-info">
            <p className="workspace__file-name">{result.filename}</p>
            <p className="workspace__file-meta">
              {formatBytes(result.size_bytes)} · PDF
              {result.detected_type && (
                <>
                  {' · '}
                  <span className="workspace__type-chip">
                    {TYPE_LABELS[result.detected_type] || result.detected_type}
                  </span>
                </>
              )}
            </p>
          </div>
        </div>
      </header>

      <div className="workspace__split">
        <div className="workspace__viewer">
          {file ? (
            <PdfViewer file={file} highlights={highlights} />
          ) : (
            <div className="workspace__viewer-empty">
              <AlertCircle size={18} strokeWidth={1.5} />
              <span>El archivo no esta disponible.</span>
            </div>
          )}
        </div>

        <aside className={`workspace__panel ${isRejection ? 'workspace__panel--rejected' : ''}`}>
          <div className="workspace__panel-head">
            <HeadIcon size={18} strokeWidth={1.5} />
            <h2 className="workspace__panel-title">{result.status}</h2>
          </div>
          {result.message && <p className="workspace__panel-msg">{result.message}</p>}

          {highlights.length > 0 && (
            <div className="hl-legend">
              <span className="hl-legend__hint">
                Resaltado en el PDF (pasá el mouse para ver el detalle):
              </span>
              <span className="hl-legend__item">
                <span className="hl-legend__swatch hl-legend__swatch--clause" />
                Cláusulas clave
              </span>
              <span className="hl-legend__item">
                <span className="hl-legend__swatch hl-legend__swatch--concern" />
                Puntos a revisar
              </span>
            </div>
          )}

          {analysis && (
            <div className="analysis">
              <div className="analysis__summary">
                <span className="analysis__label">Resumen</span>
                <p className="analysis__summary-body">{analysis.summary}</p>
              </div>

              <div className="analysis__meta">
                <div className="analysis__meta-item">
                  <span className="analysis__label">
                    <FileSignature size={12} strokeWidth={1.5} /> Tipo de contrato
                  </span>
                  <p>{analysis.contract_type}</p>
                </div>
                {analysis.parties?.length > 0 && (
                  <div className="analysis__meta-item">
                    <span className="analysis__label">
                      <Users size={12} strokeWidth={1.5} /> Partes
                    </span>
                    <ul className="analysis__parties">
                      {analysis.parties.map((p, i) => (
                        <li key={i}>{p}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {analysis.key_clauses?.length > 0 && (
                <div className="analysis__section">
                  <h3 className="analysis__section-title">Cláusulas clave</h3>
                  <ul className="analysis__clauses">
                    {analysis.key_clauses.map((c, i) => (
                      <li key={i} className="clause">
                        <span className="clause__index">{String(i + 1).padStart(2, '0')}</span>
                        <div>
                          <p className="clause__title">{c.title}</p>
                          <p className="clause__desc">{c.description}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {analysis.potential_concerns?.length > 0 && (
                <div className="analysis__section">
                  <h3 className="analysis__section-title">Puntos a revisar</h3>
                  <ul className="analysis__concerns">
                    {analysis.potential_concerns.map((c, i) => (
                      <li key={i}>
                        <AlertTriangle size={14} strokeWidth={1.5} />
                        <span>{c.text}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <Disclaimer compact />
        </aside>
      </div>
    </div>
  )
}
