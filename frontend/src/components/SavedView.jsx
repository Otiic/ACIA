import { useEffect, useState } from 'react'
import {
  FileText,
  ShoppingCart,
  Briefcase,
  Home,
  Trash2,
  Loader2,
  AlertCircle,
  FolderOpen,
  Clock,
} from 'lucide-react'
import { listContracts, getContract, getContractFile, deleteContract } from '../api/client'
import AnalysisWorkspace from './AnalysisWorkspace'
import { formatBytes, formatDate, TYPE_LABELS } from '../lib/format'
import './SavedView.css'

const TYPE_ICON = {
  compraventa: ShoppingCart,
  trabajo: Briefcase,
  alquiler: Home,
}

export default function SavedView({ mode = 'contracts' }) {
  const [items, setItems] = useState(null) // null = cargando
  const [error, setError] = useState(null)
  const [opening, setOpening] = useState(false)
  const [selected, setSelected] = useState(null) // { result, file }

  const isHistory = mode === 'history'

  const load = async () => {
    setError(null)
    try {
      const data = await listContracts()
      setItems(data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'No se pudo cargar la lista.')
      setItems([])
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleOpen = async (id) => {
    setOpening(true)
    setError(null)
    try {
      const [detail, blob] = await Promise.all([getContract(id), getContractFile(id)])
      setSelected({
        result: {
          filename: detail.filename,
          size_bytes: detail.size_bytes,
          detected_type: detail.detected_type,
          status: 'Analizado',
          message: `Guardado el ${formatDate(detail.created_at)}`,
          analysis: detail.analysis,
        },
        file: blob,
      })
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'No se pudo abrir el contrato.')
    } finally {
      setOpening(false)
    }
  }

  const handleDelete = async (id, e) => {
    e.stopPropagation()
    if (!confirm('¿Eliminar este contrato y su análisis? Esta acción no se puede deshacer.')) {
      return
    }
    try {
      await deleteContract(id)
      setItems((prev) => prev.filter((c) => c.id !== id))
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'No se pudo eliminar.')
    }
  }

  // Vista de análisis de un contrato abierto.
  if (selected) {
    return (
      <AnalysisWorkspace
        result={selected.result}
        file={selected.file}
        onBack={() => setSelected(null)}
        backLabel={isHistory ? 'Volver al historial' : 'Volver a mis contratos'}
      />
    )
  }

  return (
    <div className="saved-view">
      <header className="saved-view__header">
        <span className="saved-view__eyebrow">{isHistory ? 'Historial' : 'Biblioteca'}</span>
        <h1 className="saved-view__title">
          {isHistory ? 'Historial de análisis' : 'Mis contratos'}
        </h1>
        <p className="saved-view__lead">
          {isHistory
            ? 'Los análisis que realizaste, del más reciente al más antiguo.'
            : 'Los contratos que subiste y se analizaron correctamente.'}
        </p>
      </header>

      {error && (
        <div className="alert alert--error">
          <AlertCircle size={16} strokeWidth={1.5} />
          <span>{error}</span>
        </div>
      )}

      {opening && (
        <div className="saved-view__overlay">
          <Loader2 size={20} className="saved-view__spinner" />
          <span>Abriendo contrato…</span>
        </div>
      )}

      {items === null ? (
        <div className="saved-view__state">
          <Loader2 size={18} className="saved-view__spinner" />
          <span>Cargando…</span>
        </div>
      ) : items.length === 0 ? (
        <div className="saved-view__empty">
          {isHistory ? <Clock size={28} strokeWidth={1.1} /> : <FolderOpen size={28} strokeWidth={1.1} />}
          <p className="saved-view__empty-title">
            {isHistory ? 'Todavía no hay análisis' : 'Todavía no guardaste contratos'}
          </p>
          <p className="saved-view__empty-hint">
            Subí y analizá un contrato y aparecerá acá automáticamente.
          </p>
        </div>
      ) : (
        <ul className="saved-list">
          {items.map((c) => {
            const Icon = TYPE_ICON[c.detected_type] || FileText
            return (
              <li
                key={c.id}
                className="saved-card"
                onClick={() => handleOpen(c.id)}
                role="button"
                tabIndex={0}
              >
                <div className="saved-card__icon">
                  <Icon size={20} strokeWidth={1.4} />
                </div>
                <div className="saved-card__body">
                  <p className="saved-card__name">{c.filename}</p>
                  <p className="saved-card__meta">
                    {c.detected_type && (
                      <span className="saved-card__chip">
                        {TYPE_LABELS[c.detected_type] || c.detected_type}
                      </span>
                    )}
                    <span>{formatDate(c.created_at)}</span>
                    {!isHistory && <span>· {formatBytes(c.size_bytes)}</span>}
                  </p>
                  {isHistory && c.summary && (
                    <p className="saved-card__summary">{c.summary}</p>
                  )}
                </div>
                <button
                  className="saved-card__delete"
                  onClick={(e) => handleDelete(c.id, e)}
                  aria-label="Eliminar"
                  title="Eliminar"
                >
                  <Trash2 size={15} strokeWidth={1.5} />
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
