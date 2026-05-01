import { useEffect, useMemo, useState } from 'react'
import { useSWRConfig } from 'swr'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle
} from '../components/ui/empty'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Input } from '../components/ui/input'
import { Spinner } from '../components/ui/spinner'
import { useDashboard, type ProductItem } from '../hooks/use-dashboard'
import { useDebounce } from '../hooks/useDebounce'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table'

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
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')


  const debouncedSearch = useDebounce(searchInput, 400);
  const salesTrendRange = useMemo<'30d' | '90d' | '180d' | '1y'>(() => {
    if (period === '365d') return '1y'
    if (period === 'all') return '30d'
    return period as '30d' | '90d' | '180d' | '1y'
  }, [period])

  useEffect(() => {
    setSearch(debouncedSearch)
    setPage(1)
  }, [debouncedSearch])

  const filters = useMemo(
    () => ({ period, category, status, search: debouncedSearch }),
    [period, category, status, debouncedSearch],
  );
  const tableParams = useMemo(
    () => ({ page, pageSize: 8, sortBy, sortOrder }),
    [page, sortBy, sortOrder],
  );
  const {
    overview,
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
  } = useDashboard(filters, tableParams, salesTrendRange);
  const { mutate } = useSWRConfig()
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

  const [syncLoading, setSyncLoading] = useState(false)
  const [syncError, setSyncError] = useState<string | null>(null)
  const [syncSuccess, setSyncSuccess] = useState(false)

  const onSyncExternal = async () => {
    setSyncLoading(true)
    setSyncError(null)
    setSyncSuccess(false)
    try {
      const resp = await fetch(`${API_BASE}/external-products/sync`, { method: 'POST' })
      if (!resp.ok) throw new Error('Erro ao sincronizar')
      setSyncSuccess(true)
      // Revalidar todas as queries para garantir que os dados mais recentes sejam exibidos após a sincronização
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
    } catch (e: any) {
      setSyncError(e?.message || 'Erro desconhecido')
    } finally {
      setSyncLoading(false)
      setTimeout(() => setSyncSuccess(false), 2000)
    }
  }

  const onFilterChange = (setter: (value: string) => void, value: string) => {
    setter(value)
    setPage(1)
  }

  const onSortChange = (field: string) => {
    if (sortBy === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortBy(field)
    setSortOrder('desc')
  }

  const resetFilters = () => {
    setPeriod('all')
    setCategory('all')
    setStatus('all')
    setSearchInput('')
    setSearch('')
    setPage(1)
    setSortBy('date')
    setSortOrder('desc')
  }

  const getSortIndicator = (field: string) => {
    if (sortBy !== field) return ''
    return sortOrder === 'asc' ? ' ↑' : ' ↓'
  }

  if (isLoading) return <div className="flex h-screen items-center justify-center">Carregando...</div>
  if (error) return (
    <ErrorMessage message={error.message || 'Erro ao carregar dashboard.'} onRetry={() => window.location.reload()} />
  )

  const periodOptions = filterOptions?.periods || []
  const categories = filterOptions?.categories || []
  const statuses = filterOptions?.statuses || []
  const productsItems = products?.items || []
  const salesTrendData = salesTrend || []
  const categoryDistributionData = categoryDistribution || []
  const topProductsData = topProducts || []
  const hasNoResults = !productsItems.length
  const hasActiveFilters =
    period !== 'all' || category !== 'all' || status !== 'all' || search.trim() !== ''
  const pieColors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6']
  const RADIAN = Math.PI / 180

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
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Dashboard Analytics</h1>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>Filtros</CardTitle>
            <div className="flex gap-2">
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
                {categories.map((item: string) => (
                  <SelectItem key={item} value={item}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {/* Região removida: não disponível na API externa */}
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
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Receita Total</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">${overview?.total_revenue?.toLocaleString()}</div>
            <p className="text-sm text-muted-foreground">{overview?.revenue_change}% este mês</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Total Pedidos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{overview?.total_orders?.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Clientes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{overview?.total_customers?.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Conversão</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{overview?.conversion_rate}%</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between gap-3">
            <CardTitle>Vendas Temporais</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            {salesTrendState === 'error' ? (
              <Empty>
                <EmptyHeader>
                  <EmptyTitle>Não foi possível carregar a tendência de vendas</EmptyTitle>
                  <EmptyDescription>O servidor retornou um erro ao consultar essa métrica.</EmptyDescription>
                </EmptyHeader>
              </Empty>
            ) : salesTrendState !== 'valid' || salesTrendData.length <= 1 ? (
              <Empty>
                <EmptyHeader>
                  <EmptyTitle>Sem dados suficientes para a tendência</EmptyTitle>
                  <EmptyDescription>{salesTrendReason || 'É necessário mais de um ponto temporal válido para renderizar a linha.'}</EmptyDescription>
                </EmptyHeader>
              </Empty>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={salesTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
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
                            Receita: R$ {revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </div>
                          <div className="text-xs text-muted-foreground">Pedidos: {orders}</div>
                        </div>
                      )
                    }}
                  />
                  <Line type="linear" dataKey="revenue" stroke="#8884d8" strokeWidth={2} dot={false} connectNulls={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Distribuição por Categoria</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
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
                  <EmptyDescription>{categoryDistributionReason || 'Não há categorias válidas para este gráfico.'}</EmptyDescription>
                </EmptyHeader>
              </Empty>
            ) : (
              <ResponsiveContainer width="100%" height="50%">
                <PieChart>
                  <Pie
                    data={categoryDistributionData}
                    dataKey="orders"
                    nameKey="category"
                    outerRadius={80}
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
            <div style={{ height: 50 }} />
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
              <ResponsiveContainer width="100%" height="45%">
                <BarChart data={topProductsData} margin={{ left: 10, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="product" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="revenue" fill="#4f46e5" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Tabela de Pedidos</CardTitle>
          <div className="text-sm text-muted-foreground">
            {products?.total || 0} resultados
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  <button className="font-medium" onClick={() => onSortChange('id')}>
                    ID{getSortIndicator('id')}
                  </button>
                </TableHead>
                <TableHead>
                  <button className="font-medium" onClick={() => onSortChange('client')}>
                    Cliente{getSortIndicator('client')}
                  </button>
                </TableHead>
                <TableHead>Categoria</TableHead>
                <TableHead>
                  <button className="font-medium" onClick={() => onSortChange('revenue')}>
                    Receita{getSortIndicator('revenue')}
                  </button>
                </TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Data</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {hasNoResults && (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                    Nenhum resultado com os filtros atuais. Ajuste os filtros ou limpe para ver todos os dados.
                  </TableCell>
                </TableRow>
              )}
              {productsItems.map((item: ProductItem) => (
                <TableRow key={item.id}>
                  <TableCell>{item.id}</TableCell>
                  <TableCell>{item.client}</TableCell>
                  <TableCell>{item.category}</TableCell>
                  <TableCell>R$ {item.revenue.toLocaleString()}</TableCell>
                  <TableCell>
                    <Badge variant={item.status === 'Completed' ? 'default' : 'secondary'}>
                      {item.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{item.date}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              Página {products?.page || 1} de {products?.total_pages || 1}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                disabled={(products?.page || 1) <= 1}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                onClick={() => setPage((prev) => Math.min(prev + 1, products?.total_pages || 1))}
                disabled={(products?.page || 1) >= (products?.total_pages || 1)}
              >
                Próxima
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

