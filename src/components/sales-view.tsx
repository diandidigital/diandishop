'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { History, Calendar, Eye } from 'lucide-react'

interface SaleItem {
  productName: string
  quantity: number
  unitPrice: number
  subtotal: number
  product?: { name: string; category?: { name: string } }
}

interface Sale {
  id: string
  total: number
  profit: number
  paymentMethod: string
  customerName: string | null
  note: string | null
  createdAt: string
  saleItems: SaleItem[]
}

function formatFCFA(amount: number): string {
  return amount.toLocaleString('fr-FR') + ' FCFA'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function SalesView() {
  const [sales, setSales] = useState<Sale[]>([])
  const [loading, setLoading] = useState(true)
  const [dateFilter, setDateFilter] = useState('')
  const [selectedSale, setSelectedSale] = useState<Sale | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  useEffect(() => {
    fetchSales()
  }, [dateFilter])

  const fetchSales = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (dateFilter) params.set('date', dateFilter)
      params.set('limit', '100')
      const res = await fetch(`/api/sales?${params}`)
      const json = await res.json()
      setSales(Array.isArray(json) ? json : [])
    } catch (err) {
      console.error('Error fetching sales:', err)
    } finally {
      setLoading(false)
    }
  }

  const openDetail = (sale: Sale) => {
    setSelectedSale(sale)
    setDetailOpen(true)
  }

  const totalFiltered = sales.reduce((sum, s) => sum + s.total, 0)
  const today = new Date().toISOString().split('T')[0]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Historique des ventes</h1>
          <p className="text-muted-foreground">Toutes vos transactions</p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="size-4 text-muted-foreground" />
          <Input
            type="date"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="w-44"
            max={today}
          />
          {dateFilter && (
            <Button variant="ghost" size="sm" onClick={() => setDateFilter('')}>
              Tout voir
            </Button>
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Nombre de ventes</p>
            <p className="text-2xl font-bold">{sales.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total des ventes</p>
            <p className="text-2xl font-bold text-primary">{formatFCFA(totalFiltered)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Bénéfice total</p>
            <p className="text-2xl font-bold text-emerald-600">
              {formatFCFA(sales.reduce((sum, s) => sum + (s.profit || 0), 0))}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Sales Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="animate-pulse text-muted-foreground">Chargement...</div>
            </div>
          ) : sales.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <History className="size-12 mb-3 opacity-30" />
              <p>Aucune vente trouvée</p>
            </div>
          ) : (
            <div className="overflow-x-auto max-h-[calc(100vh-26rem)] overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Articles</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead>Paiement</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sales.map((sale) => (
                    <TableRow key={sale.id}>
                      <TableCell className="text-sm">{formatDate(sale.createdAt)}</TableCell>
                      <TableCell className="text-sm">
                        {sale.saleItems.length} article{sale.saleItems.length !== 1 ? 's' : ''}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatFCFA(sale.total)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {sale.paymentMethod === 'cash' ? 'Espèces' : 'Mobile Money'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {sale.customerName || '—'}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDetail(sale)}
                        >
                          <Eye className="size-4 mr-1" />
                          Détail
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Détail de la vente</DialogTitle>
          </DialogHeader>
          {selectedSale && (
            <div className="space-y-4">
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Date</span>
                <span>{formatDate(selectedSale.createdAt)}</span>
              </div>
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Mode de paiement</span>
                <span>{selectedSale.paymentMethod === 'cash' ? 'Espèces' : 'Mobile Money'}</span>
              </div>
              {selectedSale.customerName && (
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>Client</span>
                  <span>{selectedSale.customerName}</span>
                </div>
              )}

              <div className="space-y-2 pt-2">
                <p className="text-sm font-medium">Articles :</p>
                {selectedSale.saleItems.map((item, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span>
                      {item.productName} x{item.quantity}
                    </span>
                    <span className="font-medium">{formatFCFA(item.subtotal)}</span>
                  </div>
                ))}
              </div>

              <div className="border-t pt-2">
                <div className="flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span className="text-primary">{formatFCFA(selectedSale.total)}</span>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
