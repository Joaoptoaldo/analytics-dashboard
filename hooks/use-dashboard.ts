import useSWR from 'swr'

type DashboardOverview = {
  total_revenue: number
  total_orders: number
  total_customers: number
  conversion_rate: number
  revenue_change: number
  orders_change: number
  customers_change: number
  conversion_change: number
}

type SalesPoint = {
  month: string
  revenue: number
  orders: number
  customers: number
}

type TrafficPoint = {
  source: string
  visitors: number
  percentage: number
}

export type ProductItem = {
  id: number
  client: string
  category: string
  revenue: number
  status: string
  region: string
  date: string
}

type ProductsResponse = {
  items: ProductItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

type FilterOption = {
  value: string
  label: string
}

type FilterOptionsResponse = {
  periods: FilterOption[]
  categories: string[]
  regions: string[]
  statuses: string[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const fetcher = async <T>(url: string): Promise<T> => {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Erro na API: ${response.status}`)
  }
  return response.json() as Promise<T>
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

  const { data: overview, error: overviewError } = useSWR<DashboardOverview>(
    `/api/overview?${baseQuery}`,
    () => fetcher<DashboardOverview>(`${API_BASE}/overview?${baseQuery}`),
  )
  const { data: sales, error: salesError } = useSWR<SalesPoint[]>(
    `/api/sales?${baseQuery}`,
    () => fetcher<SalesPoint[]>(`${API_BASE}/sales?${baseQuery}`),
  )
  const { data: traffic, error: trafficError } = useSWR<TrafficPoint[]>(
    `/api/traffic?${baseQuery}`,
    () => fetcher<TrafficPoint[]>(`${API_BASE}/traffic?${baseQuery}`),
  )
  const useExternal = import.meta.env.VITE_USE_EXTERNAL === 'true'
  const productsPath = useExternal ? 'external-products' : 'products'

  const { data: products, error: productsError } = useSWR<ProductsResponse>(
    `/api/${productsPath}?${productsQuery}`,
    () => fetcher<ProductsResponse>(`${API_BASE}/${productsPath}?${productsQuery}`),
  )
  const { data: filterOptions, error: filterOptionsError } = useSWR<FilterOptionsResponse>(
    '/api/filters',
    () => fetcher<FilterOptionsResponse>(`${API_BASE}/filters`),
  )

  const error =
    overviewError ??
    salesError ??
    trafficError ??
    productsError ??
    filterOptionsError

  const isLoading =
    !overview ||
    !sales ||
    !traffic ||
    !products ||
    !filterOptions

  return {
    overview,
    sales,
    traffic,
    products,
    filterOptions,
    isLoading,
    error,
  }
}

