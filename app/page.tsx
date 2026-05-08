'use client'

import * as React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { SidebarInset, SidebarTrigger } from '../components/ui/sidebar'
import { useToast } from '../hooks/use-toast'

// placeholder para dados 
const mockData = {
  totalRevenue: '$1,234,567',
  totalOrders: '12,345',
  totalCustomers: '5,678',
  conversionRate: '3.2%',
  revenueChange: '+12.5%',
  ordersChange: '+8.2%'
}

export default function Dashboard() {
  const { toast } = useToast()

  React.useEffect(() => {
    toast({
      title: 'Bem-vindo ao Dashboard!',
      description: 'Dashboard carregado. Use o formulário para filtrar dados.',
    })
  }, [toast])

  return (
    <div className="flex min-h-screen w-full flex-col bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <SidebarTrigger className="mr-2 md:hidden" />
          <SidebarTrigger className="mr-2 hidden md:block" />
          <div className="flex w-full items-center justify-between">
            <h1 className="text-xl font-semibold">Dashboard Analytics</h1>
          </div>
        </div>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <SidebarInset>
          <div className="container flex flex-1 flex-col gap-6 p-8">
            {/* KPIs */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Receita Total</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mockData.totalRevenue}</div>
                  <p className="text-xs text-muted-foreground">
                    +{mockData.revenueChange} vs mês anterior
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Pedidos</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mockData.totalOrders}</div>
                  <p className="text-xs text-muted-foreground">
                    +{mockData.ordersChange}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Clientes</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mockData.totalCustomers}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Conversão</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mockData.conversionRate}</div>
                </CardContent>
              </Card>
            </div>
            {/* placeholder gráficos */}
            <Card>
              <CardHeader>
                <CardTitle>Vendas Mensais (Recharts próximo)</CardTitle>
                <CardDescription>Dados do backend via API configurada</CardDescription>
              </CardHeader>
              <CardContent className="h-64 bg-muted/30 rounded-md flex items-center justify-center text-muted-foreground">
                Aguardando dados da API...
              </CardContent>
            </Card>
          </div>
        </SidebarInset>
      </div>
    </div>
  )
}
