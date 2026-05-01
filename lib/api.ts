export type ApiEnvelope<T> = {
  state?: 'valid' | 'no_data' | 'error'
  reason?: string
  data?: T
}

export function unwrapApiResponse<T>(response: unknown): T[] {
  if (!response || typeof response !== 'object') return []

  const envelope = response as ApiEnvelope<T[]>
  if (envelope.state !== 'valid') return []
  if (!Array.isArray(envelope.data)) return []

  return envelope.data
}

export async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Erro na API: ${response.status}`)
  }
  return response.json() as Promise<T>
}