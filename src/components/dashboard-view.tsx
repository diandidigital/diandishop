'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  DollarSign,
  ShoppingCart,
  Package,
  AlertTriangle,
  TrendingUp,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface DashboardData {
  todayRevenue: number
  todaySaleCount: number
  productCount: number
  lowStockCount: number
  lowStockProducts: { name: string; stock: number; minStock: number }[]
  topProducts: { productName: string; totalSold: number }[]
  recentSales: {
    id: string
    total: number
    paymentMethod: string
    customerName: string | null
    createdAt: string
    saleItems: { productName: string; quantity: number }[]
  }[]
  weeklyData: { date: string; total: number }[]
}

function formatFCFA(amount: number): string {
  return amount.toLocaleString('fr-FR') + ' FCFA'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDay(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' })
}

export function DashboardView() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const res = await fetch('/api/dashboard')
      const json = await res.json()
      setData(json)
    } catch (err) {
      console.error('Error fetching dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-muted-foreground">Chargement du tableau de bord...</div>
      </div>
    )
  }

  const stats = [
    {
      title: "Chiffre d'affaires du jour",
      value: formatFCFA(data.todayRevenue),
      icon: <DollarSign className="size-5" />,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
    {
      title: 'Ventes du jour',
      value: data.todaySaleCount.toString(),
      icon: <ShoppingCart className="size-5" />,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
    {
      title: 'Produits en stock',
      value: data.productCount.toString(),
      icon: <Package className="size-5" />,
      color: 'text-teal-600',
      bg: 'bg-teal-50',
    },
    {
      title: 'Alertes de stock',
      value: data.lowStockCount.toString(),
      icon: <AlertTriangle className="size-5" />,
      color: data.lowStockCount > 0 ? 'text-red-600' : 'text-green-600',
      bg: data.lowStockCount > 0 ? 'bg-red-50' : 'bg-green-50',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Tableau de bord</h1>
        <p className="text-muted-foreground">Vue d&#39;ensemble de votre boutique</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.title}</p>
                  <p className="text-2xl font-bold mt-1">{stat.value}</p>
                </div>
                <div className={`${stat.bg} p-2 rounded-lg ${stat.color}`}>
                  {stat.icon}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekly Sales Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp className="size-4" />
              Ventes de la semaine
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatDay}
                    fontSize={12}
                    tick={{ fill: '#6b7280' }}
                  />
                  <YAxis fontSize={12} tick={{ fill: '#6b7280' }} />
                  <Tooltip
                    formatter={(value: number) => [formatFCFA(value), 'Total']}
                    labelFormatter={formatDay}
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid #e5e7eb',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                    }}
                  />
                  <Bar
                    dataKey="total"
                    fill="#10b981"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={50}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Top Products */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Produits les plus vendus</CardTitle>
          </CardHeader>
          <CardContent>
            {data.topProducts.length === 0 ? (
              <p className="text-muted-foreground text-sm">Aucune vente enregistrée</p>
            ) : (
              <div className="space-y-3">
                {data.topProducts.map((product, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="flex size-7 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold">
                        {i + 1}
                      </span>
                      <span className="text-sm font-medium">{product.productName}</span>
                    </div>
                    <Badge variant="secondary">{product.totalSold} vendus</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Sales */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Ventes récentes</CardTitle>
        </CardHeader>
        <CardContent>
          {data.recentSales.length === 0 ? (
            <p className="text-muted-foreground text-sm">Aucune vente récente</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-2 font-medium text-muted-foreground">Date</th>
                    <th className="pb-2 font-medium text-muted-foreground">Articles</th>
                    <th className="pb-2 font-medium text-muted-foreground">Total</th>
                    <th className="pb-2 font-medium text-muted-foreground">Paiement</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recentSales.map((sale) => (
                    <tr key={sale.id} className="border-b last:border-0">
                      <td className="py-2">{formatDate(sale.createdAt)}</td>
                      <td className="py-2">
                        {sale.saleItems.map((item) => `${item.productName} x${item.quantity}`).join(', ')}
                      </td>
                      <td className="py-2 font-semibold">{formatFCFA(sale.total)}</td>
                      <td className="py-2">
                        <Badge variant="outline" className="text-xs">
                          {sale.paymentMethod === 'cash' ? 'Espèces' : 'Mobile Money'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Low Stock Alerts */}
      {data.lowStockCount > 0 && (
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-red-700">
              <AlertTriangle className="size-4" />
              Alertes de stock ({data.lowStockCount})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {data.lowStockProducts.map((p, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg bg-red-50 p-3">
                  <span className="text-sm font-medium">{p.name}</span>
                  <Badge variant="destructive" className="text-xs">
                    {p.stock} / {p.minStock}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
