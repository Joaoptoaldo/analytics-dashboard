import useSWR from 'swr'
const API_BASE = ((import.meta as any).env?.VITE_API_BASE_URL as string) || 'http://localhost:8000/api'

const fetcher = async (url: string) => {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Erro na API: ${response.status}`)
  }
  return response.json()
}

export type DashboardFilters = {
  period: string
  category: string
  region: string
  status: string
  search: string
}

type TableParams = {
  page: number
  pageSize: number
  sortBy: string
  sortOrder: 'asc' | 'desc'
}

function toQueryString(filters: DashboardFilters, tableParams?: TableParams) {
  const query = new URLSearchParams({
    period: filters.period,
    category: filters.category,
    region: filters.region,
    status: filters.status,
    search: filters.search,
  })

  if (tableParams) {
    query.set('page', String(tableParams.page))
    query.set('page_size', String(tableParams.pageSize))
    query.set('sort_by', tableParams.sortBy)
    query.set('sort_order', tableParams.sortOrder)
  }

  return query.toString()
}

export function useDashboard(filters: DashboardFilters, tableParams: TableParams) {
  const baseQuery = toQueryString(filters)
  const productsQuery = toQueryString(filters, tableParams)

  const { data: overview, error: overviewError } = useSWR(
    `/api/overview?${baseQuery}`,
    () => fetcher(`${API_BASE}/overview?${baseQuery}`),
  )
  const { data: sales } = useSWR(
    `/api/sales?${baseQuery}`,
    () => fetcher(`${API_BASE}/sales?${baseQuery}`),
  )
  const { data: traffic } = useSWR(
    `/api/traffic?${baseQuery}`,
    () => fetcher(`${API_BASE}/traffic?${baseQuery}`),
  )
  const { data: products } = useSWR(
    `/api/products?${productsQuery}`,
    () => fetcher(`${API_BASE}/products?${productsQuery}`),
  )
  const { data: filterOptions } = useSWR('/api/filters', () => fetcher(`${API_BASE}/filters`))

  return {
    overview,
    sales,
    traffic,
    products,
    filterOptions,
    isLoading: !overview && !overviewError,
    error: overviewError,
  }
}

