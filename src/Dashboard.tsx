import { useMemo, useState } from 'react'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { useSWRConfig } from 'swr'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Input } from '../components/ui/input'
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
  CartesianGrid,
  Cell,
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
  const [region, setRegion] = useState('all')
  const [status, setStatus] = useState('all')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')


  const debouncedSearch = useDebounce(search, 400);
  const filters = useMemo(
    () => ({ period, category, region, status, search: debouncedSearch }),
    [period, category, region, status, debouncedSearch],
  );
  const tableParams = useMemo(
    () => ({ page, pageSize: 8, sortBy, sortOrder }),
    [page, sortBy, sortOrder],
  );
  const { overview, sales, traffic, products, filterOptions, isLoading, error } = useDashboard(filters, tableParams);
  const { mutate } = useSWRConfig()
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

  const onSyncExternal = async () => {
    try {
      await fetch(`${API_BASE}/external-products/sync`, { method: 'POST' })
      // revalidate both possible cache keys
      const productsQuery = `period=${filters.period}&category=${filters.category}&region=${filters.region}&status=${filters.status}&search=${filters.search}&page=${tableParams.page}&page_size=${tableParams.pageSize}&sort_by=${tableParams.sortBy}&sort_order=${tableParams.sortOrder}`
      await mutate(`/api/external-products?${productsQuery}`)
      await mutate(`/api/products?${productsQuery}`)
    } catch (e) {
      console.error('Sync failed', e)
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
    setRegion('all')
    setStatus('all')
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
  if (error) return <div className="flex h-screen items-center justify-center">Erro ao carregar dashboard.</div>

  const periodOptions = filterOptions?.periods || []
  const categories = filterOptions?.categories || []
  const regions = filterOptions?.regions || []
  const statuses = filterOptions?.statuses || []
  const productsItems = products?.items || []
  const trafficData = traffic || []
  const hasNoResults = !productsItems.length
  const hasActiveFilters =
    period !== 'all' || category !== 'all' || region !== 'all' || status !== 'all' || search.trim() !== ''
  const pieColors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6']

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Dashboard Analytics</h1>

      <Card>
        <CardHeader>
            <div className="flex items-center justify-between gap-3">
            <CardTitle>Filtros</CardTitle>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onSyncExternal}>Sincronizar API externa</Button>
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
            <Select value={region} onValueChange={(value) => onFilterChange(setRegion, value)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Região" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas regiões</SelectItem>
                {regions.map((item: string) => (
                  <SelectItem key={item} value={item}>
                    {item}
                  </SelectItem>
                ))}
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
              placeholder="Buscar cliente/categoria/região"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value)
                setPage(1)
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
          <CardHeader>
            <CardTitle>Vendas Mensais</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sales}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="revenue" stroke="#8884d8" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Distribuição por Região</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={trafficData} dataKey="visitors" nameKey="source" outerRadius={100} label>
                  {trafficData.map((_: unknown, index: number) => (
                    <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
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
                <TableHead>Região</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {hasNoResults && (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
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
                  <TableCell>{item.region}</TableCell>
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

