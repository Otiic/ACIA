import { useRef, useState } from 'react'
import {
  FileText,
  UploadCloud,
  AlertCircle,
  X,
  ShoppingCart,
  Briefcase,
  Home,
  Info,
} from 'lucide-react'
import { uploadContract } from '../api/client'
import AnalysisWorkspace from './AnalysisWorkspace'
import Disclaimer from './Disclaimer'
import { formatBytes } from '../lib/format'
import './UploadView.css'

const ACCEPTED = 'application/pdf'

const SUPPORTED_TYPES = [
  { id: 'compraventa', label: 'Compraventa', icon: ShoppingCart },
  { id: 'trabajo', label: 'Trabajo', icon: Briefcase },
  { id: 'alquiler', label: 'Alquiler de inmueble', icon: Home },
]

export default function UploadView() {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('idle') // idle | uploading | success | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSelect = (selected) => {
    if (!selected) return
    if (selected.type !== ACCEPTED) {
      setError('El archivo debe ser un PDF.')
      setStatus('error')
      return
    }
    setError(null)
    setFile(selected)
    setStatus('idle')
    setResult(null)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files?.[0]
    handleSelect(dropped)
  }

  const handleUpload = async () => {
    if (!file) return
    setStatus('uploading')
    setProgress(0)
    setError(null)
    try {
      const data = await uploadContract(file, setProgress)
      setResult(data)
      setStatus('success')
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error al subir el archivo.')
      setStatus('error')
    }
  }

  const reset = () => {
    setFile(null)
    setProgress(0)
    setStatus('idle')
    setResult(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  // ============= WORKSPACE: PDF + analisis lado a lado =============
  if (result) {
    return (
      <AnalysisWorkspace
        result={result}
        file={file}
        onBack={reset}
        backLabel="Subir otro contrato"
      />
    )
  }

  // ============= INTAKE: dropzone para subir =============
  return (
    <div className="upload-view">
      <header className="upload-view__header">
        <span className="upload-view__eyebrow">Nuevo análisis</span>
        <h1 className="upload-view__title">
          Subí un contrato para <em>analizarlo</em>.
        </h1>
        <p className="upload-view__lead">
          Trabajamos sobre documentos PDF. Una vez procesado, la inteligencia revisará
          el texto, identificará cláusulas relevantes y te devolverá un resumen
          comprensible.
        </p>

        <aside className="supported-types" aria-label="Tipos de contrato soportados">
          <div className="supported-types__head">
            <Info size={13} strokeWidth={1.5} />
            <span>Por ahora analizamos solo estos tres tipos de contrato:</span>
          </div>
          <ul className="supported-types__list">
            {SUPPORTED_TYPES.map((t) => {
              const Icon = t.icon
              return (
                <li key={t.id} className="supported-types__item">
                  <Icon size={14} strokeWidth={1.5} />
                  <span>{t.label}</span>
                </li>
              )
            })}
          </ul>
        </aside>
      </header>

      <section className="upload-view__panel">
        {!file && (
          <div
            className={`dropzone ${dragging ? 'is-dragging' : ''}`}
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
          >
            <div className="dropzone__icon">
              <UploadCloud size={28} strokeWidth={1.25} />
            </div>
            <div className="dropzone__text">
              <p className="dropzone__title">Arrastrá tu contrato aquí</p>
              <p className="dropzone__hint">
                o <span className="dropzone__link">elegí un archivo</span> · solo PDF
              </p>
            </div>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              hidden
              onChange={(e) => handleSelect(e.target.files?.[0])}
            />
          </div>
        )}

        {file && (
          <div className="file-card">
            <div className="file-card__icon">
              <FileText size={22} strokeWidth={1.25} />
            </div>
            <div className="file-card__info">
              <p className="file-card__name">{file.name}</p>
              <p className="file-card__meta">{formatBytes(file.size)} · PDF</p>
              {status === 'uploading' && (
                <div className="progress">
                  <div className="progress__bar" style={{ width: `${progress}%` }} />
                </div>
              )}
            </div>
            <button
              className="file-card__remove"
              onClick={reset}
              aria-label="Quitar archivo"
              disabled={status === 'uploading'}
            >
              <X size={16} strokeWidth={1.5} />
            </button>
          </div>
        )}

        {error && (
          <div className="alert alert--error">
            <AlertCircle size={16} strokeWidth={1.5} />
            <span>{error}</span>
          </div>
        )}

        {file && (
          <div className="upload-view__actions">
            <button
              className="btn btn--primary"
              onClick={handleUpload}
              disabled={status === 'uploading'}
            >
              {status === 'uploading' ? `Subiendo… ${progress}%` : 'Analizar contrato'}
            </button>
            <button className="btn btn--ghost" onClick={reset} disabled={status === 'uploading'}>
              Cancelar
            </button>
          </div>
        )}
      </section>

      <Disclaimer />
    </div>
  )
}
