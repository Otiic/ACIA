import axios from 'axios'

// Identificador anonimo por navegador (no hay login). Se persiste en
// localStorage y se manda en cada request para separar los contratos por usuario.
function getClientId() {
  let id = localStorage.getItem('aca_client_id')
  if (!id) {
    id = (crypto.randomUUID?.() || `c-${Date.now()}-${Math.random().toString(36).slice(2)}`)
    localStorage.setItem('aca_client_id', id)
  }
  return id
}

export const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
})

// Adjunta el client-id a todas las requests.
api.interceptors.request.use((config) => {
  config.headers['X-Client-Id'] = getClientId()
  return config
})

export async function uploadContract(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await api.post('/contracts/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total && onProgress) {
        onProgress(Math.round((e.loaded * 100) / e.total))
      }
    },
  })
  return data
}

export async function listContracts() {
  const { data } = await api.get('/contracts')
  return data
}

export async function getContract(id) {
  const { data } = await api.get(`/contracts/${id}`)
  return data
}

// Descarga el PDF guardado como Blob (incluye el header de client-id).
export async function getContractFile(id) {
  const { data } = await api.get(`/contracts/${id}/file`, { responseType: 'blob' })
  return data
}

export async function deleteContract(id) {
  await api.delete(`/contracts/${id}`)
}
