export type ApiEnvelope<T> = {
  state?: 'valid' | 'no_data' | 'error'
  reason?: string
  data?: T
}

export function getRequiredApiBaseUrl(): string {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

  if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL is not defined')
  }

  return apiBaseUrl
}

export function getRequiredInternalApiBaseUrl(): string {
  const apiBaseUrl = getRequiredApiBaseUrl()

  if (!apiBaseUrl.endsWith('/api')) {
    throw new Error('VITE_API_BASE_URL must end with /api')
  }

  return `${apiBaseUrl.slice(0, -4)}/internal`
}

export function getOptionalSyncToken(): string | null {
  const token = import.meta.env.VITE_EXTERNAL_SYNC_TOKEN?.trim()
  return token || null
}

export async function fetchSyncWithToken(url: string, token: string | null): Promise<Response> {
  const headers: Record<string, string> = {}
  if (token) {
    headers['x-internal-token'] = token
  }
  return fetch(url, {
    method: 'POST',
    headers,
  })
}

export function unwrapApiResponse<T>(response: unknown): T[] {
  if (!response || typeof response !== 'object') return []

  const envelope = response as ApiEnvelope<T[]>
  if (envelope.state !== 'valid') return []
  if (!Array.isArray(envelope.data)) return []

  return envelope.data
}

export async function fetchJson<T>(url: string, timeoutMs = 10000): Promise<T> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(url, { signal: controller.signal })
    if (!response.ok) {
      throw new Error(`Erro na API: ${response.status}`)
    }
    return response.json() as Promise<T>
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('Tempo limite da requisição atingido', { cause: error })
    }
    throw error
  } finally {
    window.clearTimeout(timeoutId)
  }
}