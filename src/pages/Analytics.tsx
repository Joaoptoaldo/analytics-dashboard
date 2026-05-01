import { ErrorMessage } from '@/components/ui/ErrorMessage';
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle
} from '@/components/ui/empty';
import { useMemo } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDashboard } from '../../hooks/use-dashboard';



export default function Analytics() {
  // Filtros simplificados para análise global
  const filters = useMemo(() => ({ period: 'all', category: 'all', status: 'all', search: '' }), []);
  const tableParams = useMemo(() => ({ page: 1, pageSize: 50, sortBy: 'date', sortOrder: 'desc' as 'desc' | 'asc' }), []);
  const {
    overview,
    salesMonthly,
    salesMonthlyState,
    salesMonthlyReason,
    ticketAverage,
    ticketAverageState,
    ticketAverageReason,
    isLoading,
    error,
  } = useDashboard(filters, tableParams);

  if (isLoading) return <div className="flex h-screen items-center justify-center">Carregando...</div>;
  if (error) return <ErrorMessage message={error.message || 'Erro ao carregar analytics.'} onRetry={() => window.location.reload()} />;

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Analytics</h1>

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
            {salesMonthlyState === 'error' ? (
              <Empty>
                <EmptyHeader>
                  <EmptyTitle>Não foi possível carregar as vendas mensais</EmptyTitle>
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
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={salesMonthly}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="revenue" stroke="#8884d8" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Receita Média</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            {ticketAverageState === 'error' ? (
              <Empty>
                <EmptyHeader>
                  <EmptyTitle>Não foi possível carregar o ticket médio</EmptyTitle>
                  <EmptyDescription>O servidor retornou um erro ao consultar essa métrica.</EmptyDescription>
                </EmptyHeader>
              </Empty>
            ) : ticketAverageState !== 'valid' || ticketAverage.length === 0 ? (
              <Empty>
                <EmptyHeader>
                  <EmptyTitle>Sem dados disponíveis</EmptyTitle>
                  <EmptyDescription>{ticketAverageReason || 'Não há valores válidos para este gráfico.'}</EmptyDescription>
                </EmptyHeader>
              </Empty>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ticketAverage}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="avg_ticket" stroke="#22c55e" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
