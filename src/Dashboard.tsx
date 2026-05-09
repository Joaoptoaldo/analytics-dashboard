import { useEffect, useMemo, useRef, useState } from 'react'
import { useSWRConfig } from 'swr'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from '../components/ui/empty'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Input } from '../components/ui/input'
import { Spinner } from '../components/ui/spinner'
import { useDashboard, type ProductItem } from '../hooks/use-dashboard'
import { useDebounce } from '../hooks/useDebounce'
import { fetchSyncWithToken, getOptionalSyncToken, getRequiredInternalApiBaseUrl } from '../lib/api'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export default function Dashboard() {
  const [period, setPeriod] = useState('all')
  const [category, setCategory] = useState('all')
  const [status, setStatus] = useState('all')
  const [searchInput, setSearchInput] = useState('')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  const debouncedSearch = useDebounce(searchInput, 400)
  const salesTrendRange = useMemo<'30d' | '90d' | '180d' | '1y'>(() => {
    if (period === '365d') return '1y'
    if (period === 'all') return '30d'
    return period as '30d' | '90d' | '180d' | '1y'
  }, [period])

  const filters = useMemo(
    () => ({ period, category, status, search: debouncedSearch }),
    [period, category, status, debouncedSearch],
  )
  const tableParams = useMemo(
    () => ({ page, pageSize: 8, sortBy, sortOrder }),
    [page, sortBy, sortOrder],
  )

  const {
    overview,
    salesMonthly,
    salesMonthlyState,
    salesMonthlyReason,
    salesTrend,
    salesTrendState,
    salesTrendReason,
    categoryDistribution,
    categoryDistributionState,
    categoryDistributionReason,
    topProducts,
    topProductsState,
    topProductsReason,
    products,
    filterOptions,
    isLoading,
    error,
  } = useDashboard(filters, tableParams, salesTrendRange)
  const { mutate } = useSWRConfig()
  const INTERNAL_API_BASE = getRequiredInternalApiBaseUrl()
  const SYNC_TOKEN = getOptionalSyncToken()

  const [syncLoading, setSyncLoading] = useState(false)
  const [syncError, setSyncError] = useState<string | null>(null)
  const [syncSuccess, setSyncSuccess] = useState(false)
  const syncSuccessTimerRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (syncSuccessTimerRef.current !== null) {
        window.clearTimeout(syncSuccessTimerRef.current)
      }
    }
  }, [])

  const onSyncExternal = async () => {
    setSyncLoading(true)
    setSyncError(null)
    setSyncSuccess(false)
    try {
      const resp = await fetchSyncWithToken(`${INTERNAL_API_BASE}/external-products/sync`, SYNC_TOKEN)
      if (!resp.ok) throw new Error('Erro ao sincronizar')
      setSyncSuccess(true)

      const overviewQuery = `period=${filters.period}&category=${filters.category}&status=${filters.status}&search=${filters.search}`
      const productsQuery = `period=${filters.period}&category=${filters.category}&status=${filters.status}&search=${filters.search}&page=${tableParams.page}&page_size=${tableParams.pageSize}&sort_by=${tableParams.sortBy}&sort_order=${tableParams.sortOrder}`
      await mutate(`/api/external-products?${productsQuery}`)
      await mutate(`/api/products?${productsQuery}`)
      await mutate(`/api/overview?${overviewQuery}`)
      await mutate('/api/filters')
      await mutate('/api/sales/monthly')
      await mutate(`/api/sales/trend?range=${salesTrendRange}`)
      await mutate('/api/metrics/ticket-average')
      await mutate('/api/distribution/category')
      await mutate('/api/top/products')
    } catch (syncException: unknown) {
      setSyncError(syncException instanceof Error ? syncException.message : 'Erro desconhecido')
    } finally {
      setSyncLoading(false)
      if (syncSuccessTimerRef.current !== null) {
        window.clearTimeout(syncSuccessTimerRef.current)
      }
      syncSuccessTimerRef.current = window.setTimeout(() => setSyncSuccess(false), 2000)
    }
  }

  const onFilterChange = (setter: (value: string) => void, value: string) => {
    setter(value)
    setPage(1)
  }

  const resetFilters = () => {
    setPeriod('all')
    setCategory('all')
    setStatus('all')
    setSearchInput('')
    setPage(1)
    setSortBy('date')
    setSortOrder('desc')
  }

  // preparar a série temporal com o mesmo significado visual dos filtros ativos
  const salesTimelineData = useMemo(() => {
    if (period === 'all') {
      return (salesMonthly || []).map((item) => {
        const [year, monthNumber] = item.month.split('-')
        return {
          period: item.month,
          label: `${monthNumber}/${year}`,
          revenue: item.revenue,
          orders: item.orders,
        }
      })
    }

    return (salesTrend || []).map((item) => {
      // Parse date correctly handling timezone (avoid UTC interpretation)
      const [year, month, day] = item.period.split('-')
      const date = new Date(Number(year), Number(month) - 1, Number(day))
      return {
        period: item.period,
        label: Number.isNaN(date.getTime())
          ? item.period
          : date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
          }),
        revenue: item.revenue,
        orders: item.orders,
      }
    })
  }, [period, salesMonthly, salesTrend])
  const activeSalesTrendState = period === 'all' ? salesMonthlyState : salesTrendState
  const activeSalesTrendReason = period === 'all' ? salesMonthlyReason : salesTrendReason
  const hasLoadedInitialData = Boolean(
    overview ||
    salesMonthly ||
    salesTrend ||
    categoryDistribution ||
    topProducts ||
    products ||
    filterOptions,
  )
  const isRefetching = isLoading && hasLoadedInitialData
  const salesTrendXAxisInterval = useMemo(() => {
    if (salesTimelineData.length <= 6) return 0
    return Math.max(Math.floor(salesTimelineData.length / 8), 0)
  }, [salesTimelineData.length])

  const formatMoney = (value?: number | null) =>
    new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(Number.isFinite(value ?? NaN) ? Number(value) : 0)

  if (isLoading && !hasLoadedInitialData) {
    return <div className="flex h-screen items-center justify-center">Carregando...</div>
  }
  if (error) {
    return (
      <ErrorMessage
        message={error.message || 'Erro ao carregar dashboard.'}
        onRetry={() => window.location.reload()}
      />
    )
  }

  const periodOptions = filterOptions?.periods || []
  const categories = filterOptions?.categories || []
  const statuses = filterOptions?.statuses || []
  const productsItems = products?.items || []
  const categoryDistributionData = categoryDistribution || []
  const topProductsData = topProducts || []
  const hasActiveFilters =
    period !== 'all' || category !== 'all' || status !== 'all' || debouncedSearch.trim() !== ''

  const salesTrendRangeLabel =
    period === 'all'
      ? 'Todo o histórico'
      : salesTrendRange === '1y'
        ? '1 ano'
        : salesTrendRange === '180d'
          ? '180 dias'
          : salesTrendRange === '90d'
            ? '90 dias'
            : '30 dias'
  const pieColors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6']
  const RADIAN = Math.PI / 180
  const canSyncExternal = Boolean(SYNC_TOKEN)

  const formatPercentChange = (value?: number | null) => {
    if (value === null || value === undefined || Number.isNaN(value)) return 'sem comparação'
    const sign = value > 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}% vs período anterior`
  }

  const renderCategoryPieLabel = ({
    cx = 0,
    cy = 0,
    midAngle = 0,
    innerRadius = 0,
    outerRadius = 0,
    percent = 0,
  }: {
    cx?: number
    cy?: number
    midAngle?: number
    innerRadius?: number
    outerRadius?: number
    percent?: number
  }) => {
    if (percent < 0.05) return null
    const radius = innerRadius + (outerRadius - innerRadius) * 1.12
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    return (
      <text
        x={x}
        y={y}
        fill="#ffffff"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={11}
        fontWeight={600}
      >
        {`${(percent * 100).toFixed(1)}%`}
      </text>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 px-4 py-6 text-slate-950 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Dashboard Analytics</h1>
        {isRefetching ? (
          <div className="text-xs text-muted-foreground">Atualizando dados filtrados...</div>
        ) : null}

        <Card className="shadow-sm">
          <CardHeader>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <CardTitle>Filtros</CardTitle>
              <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-end">
                <Button variant="outline" onClick={onSyncExternal} disabled={syncLoading || !canSyncExternal}>
                  {syncLoading && <Spinner />}
                  {syncLoading ? 'Sincronizando...' : syncSuccess ? 'Sincronizado!' : canSyncExternal ? 'Sincronizar API externa' : 'Sync desabilitado'}
                </Button>
                {syncError && <span className="text-xs text-destructive">{syncError}</span>}
                <Button variant="outline" onClick={resetFilters} disabled={!hasActiveFilters}>
                  Limpar filtros
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
              <Select value={period} onValueChange={(value) => onFilterChange(setPeriod, value)}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Período" />
                </SelectTrigger>
                <SelectContent>
                  {periodOptions.map((item: { value: string; label: string }) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={category} onValueChange={(value) => onFilterChange(setCategory, value)}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Categoria" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas categorias</SelectItem>
                  {categories.length > 0 ? (
                    categories.map((item: string) => (
                      <SelectItem key={item} value={item}>
                        {item}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="all" disabled>
                      Nenhuma categoria disponível
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
              <Select value={status} onValueChange={(value) => onFilterChange(setStatus, value)}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos status</SelectItem>
                  {statuses.map((item: string) => (
                    <SelectItem key={item} value={item}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                placeholder="Buscar cliente/categoria"
                value={searchInput}
                onChange={(event) => {
                  setSearchInput(event.target.value)
                  setPage(1)
                }}
              />
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Receita Total</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{formatMoney(overview?.total_revenue)}</div>
              <p className="text-sm text-muted-foreground">{formatPercentChange(overview?.revenue_change)}</p>
            </CardContent>
          </Card>
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Total Pedidos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{overview?.total_orders?.toLocaleString()}</div>
              <p className="text-sm text-muted-foreground">{formatPercentChange(overview?.orders_change)}</p>
            </CardContent>
          </Card>
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Clientes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{overview?.total_customers?.toLocaleString()}</div>
              <p className="text-sm text-muted-foreground">{formatPercentChange(overview?.customers_change)}</p>
            </CardContent>
          </Card>
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Conversão</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{overview?.conversion_rate}%</div>
              <p className="text-sm text-muted-foreground">{formatPercentChange(overview?.conversion_change)}</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <Card className="shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between gap-3">
              <div>
                <CardTitle>Vendas no tempo - série {period === 'all' ? 'mensal' : 'diária'}</CardTitle>
                <p className="text-sm text-muted-foreground">Janela ativa: {salesTrendRangeLabel}</p>
              </div>
            </CardHeader>
            <CardContent className="h-80">
              {activeSalesTrendState === 'error' ? (
                <Empty>
                  <EmptyHeader>
                    <EmptyTitle>Não foi possível carregar a tendência de vendas</EmptyTitle>
                    <EmptyDescription>O servidor retornou um erro ao consultar essa métrica.</EmptyDescription>
                  </EmptyHeader>
                </Empty>
              ) : activeSalesTrendState !== 'valid' || salesTimelineData.length <= 1 ? (
                <Empty>
                  <EmptyHeader>
                    <EmptyTitle>Sem dados suficientes para a tendência</EmptyTitle>
                    <EmptyDescription>
                      {activeSalesTrendReason || 'É necessário mais de um ponto temporal válido para renderizar a linha.'}
                    </EmptyDescription>
                  </EmptyHeader>
                </Empty>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={salesTimelineData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="label"
                      minTickGap={50}
                      tick={({ x = 0, y = 0, payload }) => {
                        const ty = y + 12
                        const text = String(payload?.value ?? '')
                        return text ? (
                          <text x={x} y={ty} transform={`rotate(-20 ${x} ${ty})`} textAnchor="end" fontSize={11}>
                            {text}
                          </text>
                        ) : null
                      }}
                    />
                    <YAxis tickFormatter={(value) => formatMoney(Number(value))} />
                    <Tooltip
                      content={({ active, payload, label }) => {
                        if (!active || !payload?.length) return null
                        const point = payload[0].payload as { revenue?: number | null; orders?: number | null }
                        const revenue = typeof point.revenue === 'number' ? point.revenue : Number(point.revenue || 0)
                        const orders = typeof point.orders === 'number' ? point.orders : Number(point.orders || 0)

                        return (
                          <div className="rounded-md border bg-background px-3 py-2 shadow-sm">
                            <div className="text-xs text-muted-foreground">Período: {String(label)}</div>
                            <div className="text-sm font-medium">Receita: {formatMoney(revenue)}</div>
                            <div className="text-xs text-muted-foreground">Pedidos: {orders}</div>
                          </div>
                        )
                      }}
                    />
                    <Line type="linear" dataKey="revenue" stroke="#4f46e5" strokeWidth={2.5} dot={false} connectNulls={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Distribuição por Categoria</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
              <div className="h-80">
                {categoryDistributionState === 'error' ? (
                  <Empty>
                    <EmptyHeader>
                      <EmptyTitle>Não foi possível carregar a distribuição</EmptyTitle>
                      <EmptyDescription>O servidor retornou um erro ao consultar essa métrica.</EmptyDescription>
                    </EmptyHeader>
                  </Empty>
                ) : categoryDistributionState !== 'valid' || categoryDistributionData.length === 0 ? (
                  <Empty>
                    <EmptyHeader>
                      <EmptyTitle>Sem dados disponíveis</EmptyTitle>
                      <EmptyDescription>
                        {categoryDistributionReason || 'Não há categorias válidas para este gráfico.'}
                      </EmptyDescription>
                    </EmptyHeader>
                  </Empty>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categoryDistributionData}
                        dataKey="orders"
                        nameKey="category"
                        outerRadius={112}
                        label={renderCategoryPieLabel}
                        labelLine={false}
                      >
                        {categoryDistributionData.map((_: unknown, index: number) => (
                          <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>

              <div className="flex h-80 flex-col gap-4">
                <div className="rounded-lg border bg-muted/30 p-3">
                  <div className="text-sm font-medium">Top products</div>
                  <div className="text-xs text-muted-foreground">Receitas mais altas no recorte atual</div>
                </div>
                <div className="flex-1">
                  {topProductsState === 'error' ? (
                    <Empty>
                      <EmptyHeader>
                        <EmptyTitle>Não foi possível carregar os top products</EmptyTitle>
                        <EmptyDescription>O servidor retornou um erro ao consultar essa métrica.</EmptyDescription>
                      </EmptyHeader>
                    </Empty>
                  ) : topProductsState !== 'valid' || topProductsData.length === 0 ? (
                    <Empty>
                      <EmptyHeader>
                        <EmptyTitle>Sem dados disponíveis</EmptyTitle>
                        <EmptyDescription>{topProductsReason || 'Não há produtos válidos para este gráfico.'}</EmptyDescription>
                      </EmptyHeader>
                    </Empty>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={topProductsData} margin={{ left: 10, right: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="product" tick={{ fontSize: 11 }} interval={0} height={58} angle={-20} textAnchor="end" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="revenue" fill="#4f46e5" radius={[6, 6, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm transition-shadow duration-200 hover:shadow-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Tabela de Pedidos</CardTitle>
              <div className="text-sm text-muted-foreground">{products?.total || 0} resultados</div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                      <th className="px-3 py-3 font-medium">ID</th>
                      <th className="px-3 py-3 font-medium">Cliente</th>
                      <th className="px-3 py-3 font-medium">Categoria</th>
                      <th className="px-3 py-3 font-medium">Receita</th>
                      <th className="px-3 py-3 font-medium">Status</th>
                      <th className="px-3 py-3 font-medium">Data</th>
                    </tr>
                  </thead>
                  <tbody>
                    {productsItems.map((item: ProductItem) => (
                      <tr key={item.id} className="border-b last:border-b-0">
                        <td className="px-3 py-3">{item.id}</td>
                        <td className="px-3 py-3">{item.client}</td>
                        <td className="px-3 py-3">{item.category}</td>
                        <td className="px-3 py-3">R$ {item.revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td className="px-3 py-3">
                          <Badge variant={item.status === 'Completed' ? 'default' : 'secondary'}>{item.status}</Badge>
                        </td>
                        <td className="px-3 py-3">{item.date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {products && products.total_pages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <Button
                    variant="outline"
                    onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                    disabled={(products?.page || 1) <= 1}
                  >
                    Anterior
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Página {products?.page || 1} de {products?.total_pages || 1}
                  </span>
                  <Button
                    variant="outline"
                    onClick={() => setPage((prev) => Math.min(prev + 1, products?.total_pages || 1))}
                    disabled={(products?.page || 1) >= (products?.total_pages || 1)}
                  >
                    Próxima
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}