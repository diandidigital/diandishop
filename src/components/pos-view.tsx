'use client'

import { useEffect, useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import {
  Search,
  Plus,
  Minus,
  Trash2,
  ShoppingCart,
  CheckCircle,
  Wallet,
  Smartphone,
  Package,
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface Product {
  id: string
  name: string
  price: number
  costPrice: number
  stock: number
  category: { name: string; color: string } | null
}

interface Category {
  id: string
  name: string
  color: string
  _count: { products: number }
}

interface CartItem {
  product: Product
  quantity: number
}

function formatFCFA(amount: number): string {
  return amount.toLocaleString('fr-FR') + ' FCFA'
}

export function PosView() {
  const { toast } = useToast()
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [cart, setCart] = useState<CartItem[]>([])
  const [paymentMethod, setPaymentMethod] = useState<'cash' | 'mobile'>('cash')
  const [amountReceived, setAmountReceived] = useState('')
  const [showConfirm, setShowConfirm] = useState(false)
  const [lastSale, setLastSale] = useState<{
    total: number
    change: number
    itemCount: number
    paymentMethod: string
  } | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchProducts = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (selectedCategory) params.set('category', selectedCategory)
      const res = await fetch(`/api/products?${params}`)
      const json = await res.json()
      setProducts(Array.isArray(json) ? json : [])
    } catch (err) {
      console.error('Error fetching products:', err)
    }
  }, [search, selectedCategory])

  const fetchCategories = async () => {
    try {
      const res = await fetch('/api/categories')
      const json = await res.json()
      setCategories(Array.isArray(json) ? json : [])
    } catch (err) {
      console.error('Error fetching categories:', err)
    }
  }

  useEffect(() => {
    const init = async () => {
      await fetchCategories()
      await fetchProducts()
      setLoading(false)
    }
    init()
  }, [fetchProducts])

  useEffect(() => {
    if (!loading) {
      fetchProducts()
    }
  }, [search, selectedCategory, fetchProducts, loading])

  const addToCart = (product: Product) => {
    if (product.stock <= 0) {
      toast({
        title: 'Stock épuisé',
        description: `${product.name} n'est plus en stock.`,
        variant: 'destructive',
      })
      return
    }

    setCart((prev) => {
      const existing = prev.find((item) => item.product.id === product.id)
      if (existing) {
        if (existing.quantity >= product.stock) {
          toast({
            title: 'Stock insuffisant',
            description: `Stock disponible: ${product.stock}`,
            variant: 'destructive',
          })
          return prev
        }
        return prev.map((item) =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        )
      }
      return [...prev, { product, quantity: 1 }]
    })
  }

  const updateQuantity = (productId: string, delta: number) => {
    setCart((prev) =>
      prev
        .map((item) => {
          if (item.product.id !== productId) return item
          const newQty = item.quantity + delta
          if (newQty <= 0) return null
          if (newQty > item.product.stock) {
            toast({
              title: 'Stock insuffisant',
              description: `Stock disponible: ${item.product.stock}`,
              variant: 'destructive',
            })
            return item
          }
          return { ...item, quantity: newQty }
        })
        .filter(Boolean) as CartItem[]
    )
  }

  const removeFromCart = (productId: string) => {
    setCart((prev) => prev.filter((item) => item.product.id !== productId))
  }

  const clearCart = () => {
    setCart([])
    setAmountReceived('')
  }

  const cartTotal = cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0)
  const cartItemCount = cart.reduce((sum, item) => sum + item.quantity, 0)
  const received = parseFloat(amountReceived) || 0
  const change = Math.max(0, received - cartTotal)

  const canCheckout = cart.length > 0 && cartTotal > 0

  const handleCheckout = () => {
    if (!canCheckout) return
    if (paymentMethod === 'cash' && received < cartTotal) {
      toast({
        title: 'Montant insuffisant',
        description: `Le montant reçu doit être au moins ${formatFCFA(cartTotal)}`,
        variant: 'destructive',
      })
      return
    }
    setShowConfirm(true)
  }

  const confirmSale = async () => {
    try {
      const items = cart.map((item) => ({
        productId: item.product.id,
        productName: item.product.name,
        quantity: item.quantity,
        unitPrice: item.product.price,
        costPrice: item.product.costPrice,
        subtotal: item.product.price * item.quantity,
      }))

      const res = await fetch('/api/sales', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items,
          paymentMethod,
          customerName: null,
          note: null,
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.error || 'Erreur lors de l\'encaissement')
      }

      setLastSale({
        total: cartTotal,
        change: paymentMethod === 'cash' ? change : 0,
        itemCount: cartItemCount,
        paymentMethod,
      })
      setShowConfirm(false)
      clearCart()
      fetchProducts()

      toast({
        title: 'Vente enregistrée !',
        description: `Total: ${formatFCFA(cartTotal)}`,
      })
    } catch (err) {
      toast({
        title: 'Erreur',
        description: err instanceof Error ? err.message : 'Erreur lors de l\'encaissement',
        variant: 'destructive',
      })
    }
  }

  const filteredProducts = products

  return (
    <div className="space-y-4 h-[calc(100vh-5rem)]">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Caisse</h1>
          <p className="text-muted-foreground">Point de vente</p>
        </div>
        <Badge variant="outline" className="text-sm">
          <ShoppingCart className="size-3 mr-1" />
          {cartItemCount} article{cartItemCount !== 1 ? 's' : ''}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0">
        {/* Product Grid */}
        <div className="lg:col-span-2 flex flex-col min-h-0">
          <div className="flex flex-col sm:flex-row gap-3 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
              <Input
                placeholder="Rechercher un produit..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={selectedCategory === null ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory(null)}
              >
                Tout
              </Button>
              {categories.map((cat) => (
                <Button
                  key={cat.id}
                  variant={selectedCategory === cat.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory(selectedCategory === cat.id ? null : cat.id)}
                >
                  <span
                    className="w-2 h-2 rounded-full mr-1.5 inline-block"
                    style={{ backgroundColor: cat.color }}
                  />
                  {cat.name}
                </Button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-pulse text-muted-foreground">Chargement des produits...</div>
            </div>
          ) : (
            <ScrollArea className="flex-1">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 pb-4">
                {filteredProducts.map((product) => {
                  const inCart = cart.find((item) => item.product.id === product.id)
                  return (
                    <button
                      key={product.id}
                      onClick={() => addToCart(product)}
                      className={`relative text-left rounded-xl border p-4 transition-all hover:shadow-md hover:border-primary/50 active:scale-[0.98] ${
                        product.stock <= 0
                          ? 'opacity-50 cursor-not-allowed border-destructive/30'
                          : inCart
                          ? 'border-primary bg-primary/5 shadow-sm'
                          : 'border-border'
                      }`}
                      disabled={product.stock <= 0}
                    >
                      {inCart && (
                        <span className="absolute -top-2 -right-2 flex size-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                          {inCart.quantity}
                        </span>
                      )}
                      <div
                        className="w-full h-8 rounded-md mb-2"
                        style={{ backgroundColor: (product.category?.color || '#10b981') + '20' } as React.CSSProperties}
                      />
                      <p className="font-medium text-sm line-clamp-2 leading-tight">{product.name}</p>
                      <p className="text-primary font-bold mt-1 text-sm">{formatFCFA(product.price)}</p>
                      <div className="flex items-center justify-between mt-1">
                        <p className="text-xs text-muted-foreground">
                          {product.category?.name || ''}
                        </p>
                        <p
                          className={`text-xs font-medium ${
                            product.stock <= 0
                              ? 'text-red-500'
                              : product.stock <= product.minStock
                              ? 'text-amber-500'
                              : 'text-emerald-600'
                          }`}
                        >
                          {product.stock <= 0
                            ? 'Épuisé'
                            : `Stock: ${product.stock}`}
                        </p>
                      </div>
                    </button>
                  )
                })}
                {filteredProducts.length === 0 && (
                  <div className="col-span-full flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <Package className="size-12 mb-3 opacity-30" />
                    <p>Aucun produit trouvé</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          )}
        </div>

        {/* Cart */}
        <div className="flex flex-col min-h-0">
          <Card className="flex flex-col flex-1 min-h-0">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <ShoppingCart className="size-4" />
                Panier
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col flex-1 min-h-0 p-4 pt-0">
              {cart.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground py-8">
                  <ShoppingCart className="size-12 mb-3 opacity-20" />
                  <p className="text-sm">Le panier est vide</p>
                  <p className="text-xs mt-1">Cliquez sur un produit pour l&#39;ajouter</p>
                </div>
              ) : (
                <>
                  <ScrollArea className="flex-1">
                    <div className="space-y-2 pr-3">
                      {cart.map((item) => (
                        <div
                          key={item.product.id}
                          className="flex items-start gap-2 rounded-lg border p-3"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{item.product.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {formatFCFA(item.product.price)} / unité
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <Button
                                variant="outline"
                                size="icon"
                                className="size-6"
                                onClick={() => updateQuantity(item.product.id, -1)}
                              >
                                <Minus className="size-3" />
                              </Button>
                              <span className="text-sm font-semibold w-8 text-center">
                                {item.quantity}
                              </span>
                              <Button
                                variant="outline"
                                size="icon"
                                className="size-6"
                                onClick={() => updateQuantity(item.product.id, 1)}
                              >
                                <Plus className="size-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="size-6 text-destructive ml-auto"
                                onClick={() => removeFromCart(item.product.id)}
                              >
                                <Trash2 className="size-3" />
                              </Button>
                            </div>
                          </div>
                          <p className="text-sm font-bold whitespace-nowrap">
                            {formatFCFA(item.product.price * item.quantity)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>

                  <Separator className="my-3" />

                  {/* Payment Method */}
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <Button
                        variant={paymentMethod === 'cash' ? 'default' : 'outline'}
                        className="flex-1"
                        size="sm"
                        onClick={() => setPaymentMethod('cash')}
                      >
                        <Wallet className="size-4 mr-2" />
                        Espèces
                      </Button>
                      <Button
                        variant={paymentMethod === 'mobile' ? 'default' : 'outline'}
                        className="flex-1"
                        size="sm"
                        onClick={() => setPaymentMethod('mobile')}
                      >
                        <Smartphone className="size-4 mr-2" />
                        Mobile Money
                      </Button>
                    </div>

                    {paymentMethod === 'cash' && (
                      <div className="space-y-2">
                        <div>
                          <label className="text-xs text-muted-foreground">
                            Montant reçu
                          </label>
                          <Input
                            type="number"
                            placeholder="0"
                            value={amountReceived}
                            onChange={(e) => setAmountReceived(e.target.value)}
                            className="mt-1"
                          />
                        </div>
                        {received >= cartTotal && received > 0 && (
                          <div className="flex justify-between text-sm rounded-lg bg-emerald-50 p-2">
                            <span className="text-muted-foreground">Monnaie à rendre</span>
                            <span className="font-bold text-emerald-700">
                              {formatFCFA(change)}
                            </span>
                          </div>
                        )}
                        <div className="flex gap-1.5 flex-wrap">
                          {[cartTotal, 5000, 10000, 20000, 50000].map((amount) => (
                            <Button
                              key={amount}
                              variant="outline"
                              size="sm"
                              className="text-xs h-7"
                              onClick={() => setAmountReceived(amount.toString())}
                            >
                              {amount.toLocaleString('fr-FR')}
                            </Button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Total */}
                    <div className="flex justify-between items-center py-2">
                      <span className="text-lg font-bold">TOTAL</span>
                      <span className="text-2xl font-bold text-primary">
                        {formatFCFA(cartTotal)}
                      </span>
                    </div>

                    <Button
                      className="w-full h-12 text-lg font-bold bg-emerald-600 hover:bg-emerald-700 text-white"
                      size="lg"
                      disabled={!canCheckout}
                      onClick={handleCheckout}
                    >
                      <CheckCircle className="size-5 mr-2" />
                      ENCAISSER
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      className="w-full text-destructive"
                      onClick={clearCart}
                    >
                      <Trash2 className="size-3 mr-1" />
                      Vider le panier
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirm} onOpenChange={setShowConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="size-5 text-emerald-600" />
              Confirmer l&#39;encaissement
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              {cart.map((item) => (
                <div key={item.product.id} className="flex justify-between text-sm">
                  <span>
                    {item.product.name} x{item.quantity}
                  </span>
                  <span className="font-medium">
                    {formatFCFA(item.product.price * item.quantity)}
                  </span>
                </div>
              ))}
              <Separator />
              <div className="flex justify-between font-bold">
                <span>Total</span>
                <span className="text-primary">{formatFCFA(cartTotal)}</span>
              </div>
              {paymentMethod === 'cash' && change > 0 && (
                <div className="flex justify-between text-sm text-emerald-700">
                  <span>Monnaie à rendre</span>
                  <span className="font-bold">{formatFCFA(change)}</span>
                </div>
              )}
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Mode de paiement</span>
                <span>{paymentMethod === 'cash' ? 'Espèces' : 'Mobile Money'}</span>
              </div>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setShowConfirm(false)}
              >
                Annuler
              </Button>
              <Button
                className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                onClick={confirmSale}
              >
                Confirmer
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Success Dialog */}
      <Dialog open={!!lastSale} onOpenChange={() => setLastSale(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-emerald-700">
              <CheckCircle className="size-6" />
              Vente enregistrée avec succès !
            </DialogTitle>
          </DialogHeader>
          {lastSale && (
            <div className="space-y-3 text-center py-4">
              <div className="text-4xl font-bold text-primary">
                {formatFCFA(lastSale.total)}
              </div>
              <p className="text-muted-foreground">
                {lastSale.itemCount} article{lastSale.itemCount !== 1 ? 's' : ''}
              </p>
              {lastSale.change > 0 && (
                <div className="rounded-lg bg-emerald-50 p-3">
                  <p className="text-sm text-muted-foreground">Monnaie rendue</p>
                  <p className="text-xl font-bold text-emerald-700">
                    {formatFCFA(lastSale.change)}
                  </p>
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                {lastSale.paymentMethod === 'cash' ? 'Espèces' : 'Mobile Money'}
              </p>
              <Button className="mt-4" onClick={() => setLastSale(null)}>
                Fermer
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}


