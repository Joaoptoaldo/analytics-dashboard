import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from '@/components/ui/empty';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useDebounce } from '@/hooks/useDebounce';
import { useEffect, useMemo, useState } from 'react';
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
} from 'recharts';
import { useDashboard, type ProductItem } from '../../hooks/use-dashboard';

export const metadata = {
  title: 'Relatórios',
  description: 'Visualize e analise os relatórios de vendas, tráfego e desempenho dos produtos.',
};

export default function Reports() {
  const [period, setPeriod] = useState('all');
  const [category, setCategory] = useState('all');
  const [status, setStatus] = useState('all');
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const debouncedSearch = useDebounce(searchInput, 400);

  useEffect(() => {
    setSearch(debouncedSearch);
    setPage(1);
  }, [debouncedSearch]);

  const filters = useMemo(() => ({ period, category, status, search }), [period, category, status, search]);
  const tableParams = useMemo(() => ({ page, pageSize: 8, sortBy, sortOrder }), [page, sortBy, sortOrder]);
  const {
    products,
    filterOptions,
    isLoading,
    error,
    salesMonthly,
    salesMonthlyState,
    salesMonthlyReason,
    categoryDistribution,
    categoryDistributionState,
    categoryDistributionReason,
  } = useDashboard(filters, tableParams);

  const onSortChange = (field: string) => {
    if (sortBy === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
      return;
    }
    setSortBy(field);
    setSortOrder('desc');
  };

  const resetFilters = () => {
    setPeriod('all');
    setCategory('all');
    setStatus('all');
    setSearchInput('');
    setSearch('');
    setPage(1);
    setSortBy('date');
    setSortOrder('desc');
  };

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold mb-4">Relatórios</h1>
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="block text-xs mb-1">Período</label>
              <Select value={period} onValueChange={setPeriod}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Período" />
                </SelectTrigger>
                <SelectContent>
                  {filterOptions?.periods.map((p: { value: string; label: string }) => (
                    <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-xs mb-1">Categoria</label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Categoria" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {filterOptions?.categories.map((c: string) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {/* Região removida: não disponível na API externa */}
            <div>
              <label className="block text-xs mb-1">Status</label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  {filterOptions?.statuses.map((s: string) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-xs mb-1">Busca</label>
              <Input value={searchInput} onChange={e => setSearchInput(e.target.value)} placeholder="Buscar cliente, categoria..." className="w-48" />
            </div>
            <Button variant="ghost" onClick={resetFilters}>Limpar</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Relatórios de Produtos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            <div className="h-48 bg-white">
              <h3 className="text-sm font-medium mb-2">Receita por mês</h3>
              {salesMonthlyState === 'error' ? (
                <Empty>
                  <EmptyHeader>
                    <EmptyTitle>Não foi possível carregar a receita mensal</EmptyTitle>
                    <EmptyDescription>O servidor retornou um erro ao consultar essa métrica.</EmptyDescription>
                  </EmptyHeader>
                </Empty>
              ) : salesMonthlyState !== 'valid' || salesMonthly.length === 0 ? (
                <Empty>
                  <EmptyHeader>
                    <EmptyTitle>Sem dados disponíveis</EmptyTitle>
                    <EmptyDescription>{salesMonthlyReason || 'Não há registros válidos com date para este gráfico.'}</EmptyDescription>
                  </EmptyHeader>
                </Empty>
              ) : (
                <ResponsiveContainer width="100%" height={160}>
                  <LineChart data={salesMonthly} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="revenue" stroke="#4f46e5" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
            <div className="h-48 bg-white">
              <h3 className="text-sm font-medium mb-2">Distribuição por Categoria</h3>
              {categoryDistributionState === 'error' ? (
                <Empty>
                  <EmptyHeader>
                    <EmptyTitle>Não foi possível carregar a distribuição</EmptyTitle>
                    <EmptyDescription>O servidor retornou um erro ao consultar essa métrica.</EmptyDescription>
                  </EmptyHeader>
                </Empty>
              ) : categoryDistributionState !== 'valid' || categoryDistribution.length === 0 ? (
                <Empty>
                  <EmptyHeader>
                    <EmptyTitle>Sem dados disponíveis</EmptyTitle>
                    <EmptyDescription>{categoryDistributionReason || 'Não há categorias válidas para este gráfico.'}</EmptyDescription>
                  </EmptyHeader>
                </Empty>
              ) : (
                <ResponsiveContainer width="100%" height={160}>
                  <PieChart>
                    <Pie data={categoryDistribution} dataKey="orders" nameKey="category" outerRadius={95} fill="#82ca9d">
                      {(categoryDistribution || []).map((entry: { category: string | null; revenue: number | null; orders: number | null }, index: number) => (
                        <Cell key={`cell-${index}`} fill={["#60a5fa", "#f97316", "#34d399", "#f472b6", "#a78bfa"][index % 5]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
          {isLoading ? (
            <div className="py-12 text-center text-muted-foreground">Carregando...</div>
          ) : error ? (
            <ErrorMessage message={error.message || 'Erro ao carregar relatórios.'} onRetry={() => window.location.reload()} />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead onClick={() => onSortChange('id')} className="cursor-pointer">ID {sortBy === 'id' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</TableHead>
                    <TableHead onClick={() => onSortChange('client')} className="cursor-pointer">Cliente {sortBy === 'client' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</TableHead>
                    <TableHead onClick={() => onSortChange('category')} className="cursor-pointer">Categoria {sortBy === 'category' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</TableHead>
                    <TableHead onClick={() => onSortChange('revenue')} className="cursor-pointer">Receita {sortBy === 'revenue' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</TableHead>
                    <TableHead onClick={() => onSortChange('status')} className="cursor-pointer">Status {sortBy === 'status' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</TableHead>
                    <TableHead onClick={() => onSortChange('date')} className="cursor-pointer">Data {sortBy === 'date' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {products?.items.map((item: ProductItem) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.id}</TableCell>
                      <TableCell>{item.client}</TableCell>
                      <TableCell>{item.category}</TableCell>
                      <TableCell>R$ {item.revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</TableCell>
                      <TableCell><Badge>{item.status}</Badge></TableCell>
                      <TableCell>{item.date}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <div className="flex justify-between items-center mt-4">
                <span className="text-xs text-muted-foreground">
                  Página {products?.page} de {products?.total_pages} — {products?.total} resultados
                </span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={products?.page === 1}>Anterior</Button>
                  <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(products?.total_pages ?? 1, p + 1))} disabled={products?.page === products?.total_pages}>Próxima</Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}