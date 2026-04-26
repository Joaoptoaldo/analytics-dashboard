import { useMemo, useState } from 'react';
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

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDashboard } from '@/hooks/use-dashboard';


export default function Analytics() {
  
  const [period, setPeriod] = useState('all');
  const filters = useMemo(() => ({ period, category: 'all', region: 'all', status: 'all', search: '' }), [period]);
  const tableParams = useMemo(() => ({ page: 1, pageSize: 100, sortBy: 'date', sortOrder: 'desc' as 'asc' | 'desc' }), []);
  const { overview, sales, traffic, isLoading, error } = 
  useDashboard(filters, tableParams);
  
  const pieColors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6'];

  if (isLoading) return <div className="flex h-screen items-center justify-center">Carregando...</div>;
  if (error) return <div className="flex h-screen items-center justify-center">Erro ao carregar analytics.</div>;

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
                <Pie data={traffic} dataKey="visitors" nameKey="source" outerRadius={100} label>
                  {traffic?.map((_: unknown, index: number) => (
                    <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
