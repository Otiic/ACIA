import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Loader2 } from 'lucide-react'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import './PdfViewer.css'

// Worker servido desde node_modules via Vite (?url importa el archivo como string URL).
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

const ZOOM_STEP = 0.15
const MIN_ZOOM = 0.6
const MAX_ZOOM = 2.2

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * Dado los text items de una pagina (pdfjs) y la lista de highlights,
 * devuelve un Map itemIndex -> { id, type } indicando que item resaltar.
 *
 * Estrategia: pdfjs parte el texto en fragmentos arbitrarios (a veces corta
 * palabras a la mitad y los espacios son inconsistentes). Para que el match sea
 * robusto, concatenamos TODOS los caracteres sin espacios y buscamos la cita
 * (tambien sin espacios) como substring. Guardamos de que item viene cada
 * caracter para mapear el rango encontrado de vuelta a los items.
 */
function computeItemHighlights(items, highlights) {
  const map = new Map()
  if (!items?.length || !highlights?.length) return map

  // norm: string en minusculas sin espacios. charItem[k] = itemIndex del char k.
  let norm = ''
  const charItem = []
  items.forEach((item, i) => {
    for (const ch of item.str || '') {
      if (/\s/.test(ch)) continue
      norm += ch.toLowerCase()
      charItem.push(i)
    }
  })

  for (const h of highlights) {
    const q = (h.quote || '').toLowerCase().replace(/\s+/g, '')
    if (q.length < 6) continue

    let from = 0
    let guard = 0
    while (guard < 50) {
      guard += 1
      const idx = norm.indexOf(q, from)
      if (idx === -1) break
      for (let k = idx; k < idx + q.length; k++) {
        const itemIdx = charItem[k]
        const existing = map.get(itemIdx)
        // Prioridad: una observacion (concern) pisa a una clausula, para que el
        // aviso no quede oculto si se solapan.
        if (!existing || (existing.type !== 'concern' && h.type === 'concern')) {
          map.set(itemIdx, { id: h.id, type: h.type })
        }
      }
      from = idx + q.length
    }
  }
  return map
}

export default function PdfViewer({ file, highlights = [] }) {
  const [numPages, setNumPages] = useState(0)
  const [page, setPage] = useState(1)
  const [zoom, setZoom] = useState(1)
  const [containerWidth, setContainerWidth] = useState(0)
  const [pageHl, setPageHl] = useState(() => new Map())
  const [tooltip, setTooltip] = useState(null) // { x, y, finding }
  const wrapRef = useRef(null)
  const textItemsRef = useRef(null)

  const docOptions = useMemo(() => ({}), [])

  // Indice id -> finding para el tooltip.
  const findingById = useMemo(() => {
    const m = new Map()
    for (const h of highlights) m.set(h.id, h)
    return m
  }, [highlights])

  // Object URL del File, creado/limpiado dentro del effect (sobrevive el doble
  // mount de StrictMode en dev).
  const [docFile, setDocFile] = useState(null)
  useEffect(() => {
    if (!file) {
      setDocFile(null)
      return
    }
    const url = URL.createObjectURL(file)
    setDocFile({ url })
    return () => URL.revokeObjectURL(url)
  }, [file])

  // Medimos el ancho disponible para que la pagina rinda al contenedor.
  useEffect(() => {
    if (!wrapRef.current) return
    const el = wrapRef.current
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) setContainerWidth(entry.contentRect.width)
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // Al cambiar de pagina, limpiamos resaltados viejos hasta recalcular.
  useEffect(() => {
    textItemsRef.current = null
    setPageHl(new Map())
    setTooltip(null)
  }, [page])

  // Si cambian los highlights (nuevo analisis) y ya tenemos el texto, recalcular.
  useEffect(() => {
    if (textItemsRef.current) {
      setPageHl(computeItemHighlights(textItemsRef.current, highlights))
    }
  }, [highlights])

  const onLoadSuccess = ({ numPages }) => {
    setNumPages(numPages)
    setPage(1)
  }

  const onGetTextSuccess = useCallback(
    (textContent) => {
      const items = textContent?.items || []
      textItemsRef.current = items
      setPageHl(computeItemHighlights(items, highlights))
    },
    [highlights],
  )

  // customTextRenderer: por cada item del texto, si esta resaltado lo envolvemos
  // en un <mark> con su color y el id del finding (para el tooltip).
  const customTextRenderer = useCallback(
    ({ str, itemIndex }) => {
      const hit = pageHl.get(itemIndex)
      const safe = escapeHtml(str)
      if (!hit) return safe
      return `<mark class="pdf-hl pdf-hl--${hit.type}" data-hl-id="${escapeHtml(
        hit.id,
      )}">${safe}</mark>`
    },
    [pageHl],
  )

  // Tooltip por delegacion: detectamos el <mark> bajo el mouse.
  const handlePointer = useCallback(
    (e) => {
      const mark = e.target.closest?.('.pdf-hl')
      if (!mark) {
        setTooltip((t) => (t ? null : t))
        return
      }
      const finding = findingById.get(mark.dataset.hlId)
      if (!finding) return
      const rect = mark.getBoundingClientRect()
      setTooltip({ x: rect.left, y: rect.top, finding })
    },
    [findingById],
  )

  const prev = () => setPage((p) => Math.max(1, p - 1))
  const next = () => setPage((p) => Math.min(numPages, p + 1))
  const zoomIn = () => setZoom((z) => Math.min(MAX_ZOOM, +(z + ZOOM_STEP).toFixed(2)))
  const zoomOut = () => setZoom((z) => Math.max(MIN_ZOOM, +(z - ZOOM_STEP).toFixed(2)))

  const pageWidth = containerWidth > 0 ? Math.max(280, (containerWidth - 32) * zoom) : undefined

  return (
    <div className="pdf-viewer">
      <div className="pdf-viewer__toolbar">
        <div className="pdf-viewer__nav">
          <button className="pdf-viewer__btn" onClick={prev} disabled={page <= 1} aria-label="Pagina anterior">
            <ChevronLeft size={16} strokeWidth={1.5} />
          </button>
          <span className="pdf-viewer__counter">
            {numPages > 0 ? `${page} / ${numPages}` : '— / —'}
          </span>
          <button className="pdf-viewer__btn" onClick={next} disabled={page >= numPages} aria-label="Pagina siguiente">
            <ChevronRight size={16} strokeWidth={1.5} />
          </button>
        </div>

        <div className="pdf-viewer__zoom">
          <button className="pdf-viewer__btn" onClick={zoomOut} disabled={zoom <= MIN_ZOOM} aria-label="Reducir">
            <ZoomOut size={14} strokeWidth={1.5} />
          </button>
          <span className="pdf-viewer__zoom-value">{Math.round(zoom * 100)}%</span>
          <button className="pdf-viewer__btn" onClick={zoomIn} disabled={zoom >= MAX_ZOOM} aria-label="Aumentar">
            <ZoomIn size={14} strokeWidth={1.5} />
          </button>
        </div>
      </div>

      <div
        className="pdf-viewer__canvas"
        ref={wrapRef}
        onMouseOver={handlePointer}
        onMouseLeave={() => setTooltip(null)}
      >
        {docFile && (
          <Document
            file={docFile}
            options={docOptions}
            onLoadSuccess={onLoadSuccess}
            loading={
              <div className="pdf-viewer__loading">
                <Loader2 size={18} className="pdf-viewer__spinner" />
                <span>Cargando documento…</span>
              </div>
            }
            error={<div className="pdf-viewer__error">No se pudo renderizar el PDF.</div>}
          >
            <Page
              pageNumber={page}
              width={pageWidth}
              renderTextLayer
              renderAnnotationLayer={false}
              customTextRenderer={customTextRenderer}
              onGetTextSuccess={onGetTextSuccess}
              loading={
                <div className="pdf-viewer__loading">
                  <Loader2 size={18} className="pdf-viewer__spinner" />
                </div>
              }
            />
          </Document>
        )}
      </div>

      {tooltip && (
        <div
          className={`pdf-tooltip pdf-tooltip--${tooltip.finding.type}`}
          style={{ left: tooltip.x, top: tooltip.y }}
          role="tooltip"
        >
          <span className="pdf-tooltip__label">{tooltip.finding.label}</span>
          <span className="pdf-tooltip__text">{tooltip.finding.text}</span>
        </div>
      )}
    </div>
  )
}
