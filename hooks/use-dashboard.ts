import { useMemo } from 'react'
import useSWR from 'swr'

import { fetchJson, getRequiredApiBaseUrl, unwrapApiResponse } from '../lib/api'

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

export type ProductItem = {
  id: number
  client: string
  category: string
  revenue: number
  status: string
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
  statuses: string[]
}

export type DashboardFilters = {
  period: string
  category: string
  status: string
  search: string
}

type TableParams = {
  page: number
  pageSize: number
  sortBy: string
  sortOrder: 'asc' | 'desc'
}

export type MetricState = 'valid' | 'no_data' | 'error'

type MetricEnvelope<T> = {
  state?: MetricState
  reason?: string
  data?: T[]
}

type SalesPoint = {
  month: string
  revenue: number | null
  orders: number | null
}

type SalesTrendRange = '30d' | '90d' | '180d' | '1y'

type SalesTrendPoint = {
  period: string
  revenue: number | null
  orders: number | null
}

type RawCategoryDistributionPoint = {
  category?: string | null
  count?: number | null
  orders?: number | null
  revenue?: number | null
}

type CategoryDistributionPoint = {
  category: string | null
  revenue: number | null
  orders: number | null
}

type RawTopProductPoint = {
  product?: string | null
  product_name?: string | null
  product_id?: number | null
  revenue?: number | null
  orders?: number | null
}

type TopProductPoint = {
  product: string | null
  revenue: number | null
  orders: number | null
}

type TicketAveragePoint = {
  month: string
  avg_ticket: number | null
}

type MetricResult<T> = {
  data: T[]
  state: MetricState
  reason?: string
  error?: Error
  isLoading: boolean
}

const API_BASE = getRequiredApiBaseUrl()
const DATA_REFRESH_INTERVAL_MS = 30000

const swrRefreshConfig = {
  refreshInterval: DATA_REFRESH_INTERVAL_MS,
  revalidateOnFocus: true,
  revalidateOnReconnect: true,
  refreshWhenHidden: false,
  keepPreviousData: true,
} as const

function toQueryString(filters: DashboardFilters, tableParams?: TableParams) {
  const query = new URLSearchParams({
    period: filters.period,
    category: filters.category,
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

function parseMetricResponse<T>(response: unknown): { data: T[]; state: MetricState; reason?: string } {
  if (!response || typeof response !== 'object') {
    return { data: [], state: 'error', reason: 'invalid_response' }
  }

  const envelope = response as MetricEnvelope<T>
  if (envelope.state === 'valid') {
    return { data: unwrapApiResponse<T>(response), state: 'valid', reason: envelope.reason }
  }

  if (envelope.state === 'no_data') {
    return { data: [], state: 'no_data', reason: envelope.reason }
  }

  return { data: [], state: 'error', reason: envelope.reason ?? 'api_error' }
}

function useMetricEndpoint<T>(key: string, url: string): MetricResult<T> {
  const { data, error, isLoading } = useSWR<MetricEnvelope<T>>(
    key,
    () => fetchJson<MetricEnvelope<T>>(url),
    swrRefreshConfig,
  )

  const parsed = useMemo(() => parseMetricResponse<T>(data), [data])

  return {
    data: parsed.data,
    state: parsed.state,
    reason: parsed.reason,
    error: error as Error | undefined,
    isLoading: isLoading || (!data && !error),
  }
}

function useSalesTrend(trendRange: SalesTrendRange, baseQuery?: string): MetricResult<SalesTrendPoint> {
  const qs = baseQuery ? `${baseQuery}&range=${trendRange}` : `range=${trendRange}`
  return useMetricEndpoint<SalesTrendPoint>(
    `/api/sales/trend?${qs}`,
    `${API_BASE}/sales/trend?${qs}`,
  )
}

export function useSales(baseQuery?: string) {
  const salesMonthly = useMetricEndpoint<SalesPoint>(
    `/api/sales/monthly${baseQuery ? `?${baseQuery}` : ''}`,
    `${API_BASE}/sales/monthly${baseQuery ? `?${baseQuery}` : ''}`,
  )
  const ticketAverage = useMetricEndpoint<TicketAveragePoint>(
    `/api/metrics/ticket-average${baseQuery ? `?${baseQuery}` : ''}`,
    `${API_BASE}/metrics/ticket-average${baseQuery ? `?${baseQuery}` : ''}`,
  )

  return {
    salesMonthly: salesMonthly.data,
    salesMonthlyState: salesMonthly.state,
    salesMonthlyReason: salesMonthly.reason,
    ticketAverage: ticketAverage.data,
    ticketAverageState: ticketAverage.state,
    ticketAverageReason: ticketAverage.reason,
    isLoading: salesMonthly.isLoading || ticketAverage.isLoading,
    error: salesMonthly.error ?? ticketAverage.error,
  }
}

export function useAnalytics() {
  const categoryDistribution = useMetricEndpoint<RawCategoryDistributionPoint>('/api/distribution/category', `${API_BASE}/distribution/category`)
  const topProducts = useMetricEndpoint<RawTopProductPoint>('/api/top/products', `${API_BASE}/top/products`)

  const normalizedCategoryDistribution: CategoryDistributionPoint[] = categoryDistribution.data.map((item) => ({
    category: item.category ?? null,
    revenue: item.revenue ?? null,
    orders: item.orders ?? item.count ?? null,
  }))

  const normalizedTopProducts: TopProductPoint[] = topProducts.data.map((item) => ({
    product: item.product ?? item.product_name ?? null,
    revenue: item.revenue ?? null,
    orders: item.orders ?? null,
  }))

  return {
    categoryDistribution: normalizedCategoryDistribution,
    categoryDistributionState: categoryDistribution.state,
    categoryDistributionReason: categoryDistribution.reason,
    topProducts: normalizedTopProducts,
    topProductsState: topProducts.state,
    topProductsReason: topProducts.reason,
    isLoading: categoryDistribution.isLoading || topProducts.isLoading,
    error: categoryDistribution.error ?? topProducts.error,
  }
}

export function useDashboard(filters: DashboardFilters, tableParams: TableParams, salesTrendRange: SalesTrendRange = '30d') {
  const baseQuery = toQueryString(filters)
  const productsQuery = toQueryString(filters, tableParams)

  const { data: overview, error: overviewError } = useSWR<DashboardOverview>(
    `/api/overview?${baseQuery}`,
    () => fetchJson<DashboardOverview>(`${API_BASE}/overview?${baseQuery}`),
    swrRefreshConfig,
  )

  const useExternal = import.meta.env.VITE_USE_EXTERNAL === 'true'
  const productsPath = useExternal ? 'external-products' : 'products'

  const { data: products, error: productsError } = useSWR<ProductsResponse>(
    `/api/${productsPath}?${productsQuery}`,
    () => fetchJson<ProductsResponse>(`${API_BASE}/${productsPath}?${productsQuery}`),
    swrRefreshConfig,
  )

  const { data: filterOptions, error: filterOptionsError } = useSWR<FilterOptionsResponse>(
    '/api/filters',
    () => fetchJson<FilterOptionsResponse>(`${API_BASE}/filters`),
    swrRefreshConfig,
  )

  const sales = useSales(baseQuery)
  const analytics = useAnalytics()
  const salesTrend = useSalesTrend(salesTrendRange, baseQuery)

  return {
    overview,
    products,
    filterOptions,
    salesMonthly: sales.salesMonthly,
    salesMonthlyState: sales.salesMonthlyState,
    salesMonthlyReason: sales.salesMonthlyReason,
    salesTrend: salesTrend.data,
    salesTrendState: salesTrend.state,
    salesTrendReason: salesTrend.reason,
    ticketAverage: sales.ticketAverage,
    ticketAverageState: sales.ticketAverageState,
    ticketAverageReason: sales.ticketAverageReason,
    categoryDistribution: analytics.categoryDistribution,
    categoryDistributionState: analytics.categoryDistributionState,
    categoryDistributionReason: analytics.categoryDistributionReason,
    topProducts: analytics.topProducts,
    topProductsState: analytics.topProductsState,
    topProductsReason: analytics.topProductsReason,
    isLoading:
      !overview ||
      !products ||
      !filterOptions ||
      sales.isLoading ||
      salesTrend.isLoading ||
      analytics.isLoading,
    error: overviewError ?? productsError ?? filterOptionsError ?? sales.error ?? salesTrend.error ?? analytics.error,
  }
}