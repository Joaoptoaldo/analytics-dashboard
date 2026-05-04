import { useMemo, useState } from 'react'
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
      setTimeout(() => setSyncSuccess(false), 2000)
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

  // preparar dados do gráfico antes de quaisquer retornos condicionais
  const salesTrendData = useMemo(() => {
    if (period === 'all') {
      const monthly = salesMonthly || []
      return monthly.map((m) => ({ period: `${m.month}-01`, revenue: m.revenue, orders: m.orders }))
    }
    return salesTrend || []
  }, [period, salesMonthly, salesTrend])
  const activeSalesTrendState = period === 'all' ? salesMonthlyState : salesTrendState
  const activeSalesTrendReason = period === 'all' ? salesMonthlyReason : salesTrendReason
  const aggregatedSalesTrend = useMemo(() => {
    if (!salesTrendData || salesTrendData.length === 0) return salesTrendData
    if (salesTrendRange !== '90d') return salesTrendData

    // agrupa por semanas (segunda-feira como início)
    const map = new Map<string, { period: string; revenue: number; orders: number }>()
    for (const p of salesTrendData) {
      const date = new Date(p.period)
      if (isNaN(date.getTime())) continue
      const day = date.getDay()
      const diffToMonday = (day + 6) % 7
      const monday = new Date(date)
      monday.setDate(date.getDate() - diffToMonday)
      monday.setHours(0, 0, 0, 0)
      const key = monday.toISOString().slice(0, 10)
      const existing = map.get(key)
      const revenue = Number(p.revenue || 0)
      const orders = Number(p.orders || 0)
      if (existing) {
        existing.revenue += revenue
        existing.orders += orders
      } else {
        map.set(key, { period: key, revenue, orders })
      }
    }

    const arr = Array.from(map.values()).sort((a, b) => (a.period < b.period ? -1 : 1))
    // formata period para dd/mm/YYYY para exibição
    return arr.map((r) => ({
      ...r, period: (() => {
        const d = new Date(r.period)
        const day = String(d.getDate()).padStart(2, '0')
        const month = String(d.getMonth() + 1).padStart(2, '0')
        return `${day}/${month}/${d.getFullYear()}`
      })()
    }))
  }, [salesTrendData, salesTrendRange])
  const salesTrendXAxisInterval = useMemo(() => {
    if (salesTrendRange === '1y') return 29
    if (salesTrendRange === '180d') return 13
    if (salesTrendRange === '90d') return 6
    return 2
  }, [salesTrendRange])

  const formatTick = (value: string, range: string) => {
    try {
      const d = new Date(value)
      if (isNaN(d.getTime())) return value
      const day = String(d.getDate()).padStart(2, '0')
      const month = String(d.getMonth() + 1).padStart(2, '0')
      return `${day}/${month}/${d.getFullYear()}`
    } catch {
      return value
    }
  }

  if (isLoading) return <div className="flex h-screen items-center justify-center">Carregando...</div>
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
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 px-4 py-6 text-slate-950 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Dashboard Analytics</h1>

        <Card className="shadow-sm transition-shadow duration-200 hover:shadow-md">
          <CardHeader>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <CardTitle>Filtros</CardTitle>
              <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-end">
                <Button variant="outline" onClick={onSyncExternal} disabled={syncLoading}>
                  {syncLoading && <Spinner />}
                  {syncLoading ? 'Sincronizando...' : syncSuccess ? 'Sincronizado!' : 'Sincronizar API externa'}
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
          <Card className="shadow-sm transition-shadow duration-200 hover:shadow-md">
            <CardHeader>
              <CardTitle>Receita Total</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">${overview?.total_revenue?.toLocaleString()}</div>
              <p className="text-sm text-muted-foreground">{formatPercentChange(overview?.revenue_change)}</p>
            </CardContent>
          </Card>
          <Card className="shadow-sm transition-shadow duration-200 hover:shadow-md">
            <CardHeader>
              <CardTitle>Total Pedidos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{overview?.total_orders?.toLocaleString()}</div>
              <p className="text-sm text-muted-foreground">{formatPercentChange(overview?.orders_change)}</p>
            </CardContent>
          </Card>
          <Card className="shadow-sm transition-shadow duration-200 hover:shadow-md">
            <CardHeader>
              <CardTitle>Clientes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{overview?.total_customers?.toLocaleString()}</div>
              <p className="text-sm text-muted-foreground">{formatPercentChange(overview?.customers_change)}</p>
            </CardContent>
          </Card>
          <Card className="shadow-sm transition-shadow duration-200 hover:shadow-md">
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
          <Card className="shadow-sm transition-shadow duration-200 hover:shadow-md">
            <CardHeader className="flex flex-row items-center justify-between gap-3">
              <div>
                <CardTitle>Vendas Temporais - série diária</CardTitle>
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
              ) : activeSalesTrendState !== 'valid' || salesTrendData.length <= 1 ? (
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
                  <LineChart data={salesTrendRange === '90d' ? aggregatedSalesTrend : salesTrendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    {/** componente de tick rotacionado para evitar sobreposição */}
                    {(() => {
                      const RotatedTick = (props: any) => {
                        const { x, y, payload } = props
                        const label = formatTick(String(payload?.value ?? ''), salesTrendRange)
                        const ty = y + 12
                        return (
                          <text x={x} y={ty} transform={`rotate(-20 ${x} ${ty})`} textAnchor="end" fontSize={11}>
                            {label}
                          </text>
                        )
                      }

                      return (
                        <XAxis dataKey="period" interval={salesTrendXAxisInterval} minTickGap={18} tick={<RotatedTick />} />
                      )
                    })()}
                    <YAxis />
                    <Tooltip
                      content={({ active, payload, label }) => {
                        if (!active || !payload?.length) return null
                        const point = payload[0].payload as { revenue?: number | null; orders?: number | null }
                        const revenue = typeof point.revenue === 'number' ? point.revenue : Number(point.revenue || 0)
                        const orders = typeof point.orders === 'number' ? point.orders : Number(point.orders || 0)

                        return (
                          <div className="rounded-md border bg-background px-3 py-2 shadow-sm">
                            <div className="text-xs text-muted-foreground">Período: {label}</div>
                            <div className="text-sm font-medium">
                              Receita: R$ {revenue.toLocaleString('pt-BR', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}
                            </div>
                            <div className="text-xs text-muted-foreground">Pedidos: {orders}</div>
                          </div>
                        )
                      }}
                    />
                    <Line type="linear" dataKey="revenue" stroke="#8884d8" strokeWidth={2.5} dot={false} connectNulls={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card className="shadow-sm transition-shadow duration-200 hover:shadow-md">
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