export function formatBytes(bytes) {
  if (!bytes) return ''
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(0)} KB`
  return `${(kb / 1024).toFixed(2)} MB`
}

export const TYPE_LABELS = {
  compraventa: 'Compraventa',
  trabajo: 'Trabajo',
  alquiler: 'Alquiler de inmueble',
  otro_contrato: 'Otro tipo de contrato',
  no_contrato: 'No es un contrato',
}

export function formatDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString('es-AR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}
