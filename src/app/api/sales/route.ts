import { db } from '@/lib/db'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const dateFilter = searchParams.get('date') || ''
    const limit = parseInt(searchParams.get('limit') || '50')

    const where: Record<string, unknown> = {}

    if (dateFilter) {
      const startDate = new Date(dateFilter)
      startDate.setHours(0, 0, 0, 0)
      const endDate = new Date(dateFilter)
      endDate.setHours(23, 59, 59, 999)
      where.createdAt = { gte: startDate, lte: endDate }
    }

    const sales = await db.sale.findMany({
      where,
      include: {
        saleItems: {
          include: { product: { select: { name: true, category: { select: { name: true } } } } },
        },
      },
      orderBy: { createdAt: 'desc' },
      take: limit,
    })

    return NextResponse.json(sales)
  } catch (error) {
    console.error('Error fetching sales:', error)
    return NextResponse.json({ error: 'Erreur lors de la récupération des ventes' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { items, paymentMethod, customerName, note } = body

    if (!items || !Array.isArray(items) || items.length === 0) {
      return NextResponse.json({ error: 'La vente doit contenir au moins un article' }, { status: 400 })
    }

    // Validate stock availability
    for (const item of items) {
      const product = await db.product.findUnique({ where: { id: item.productId } })
      if (!product) {
        return NextResponse.json({ error: `Produit "${item.productName}" introuvable` }, { status: 400 })
      }
      if (product.stock < item.quantity) {
        return NextResponse.json(
          { error: `Stock insuffisant pour "${item.productName}". Disponible: ${product.stock}` },
          { status: 400 }
        )
      }
    }

    const total = items.reduce((sum: number, item: { subtotal: number }) => sum + item.subtotal, 0)
    const profit = items.reduce((sum: number, item: { quantity: number; unitPrice: number; costPrice: number }) => {
      return sum + (item.quantity * (item.unitPrice - (item.costPrice || 0)))
    }, 0)

    const sale = await db.sale.create({
      data: {
        total,
        profit,
        paymentMethod: paymentMethod || 'cash',
        customerName: customerName || null,
        note: note || null,
        saleItems: {
          create: items.map((item: { productId: string; productName: string; quantity: number; unitPrice: number; subtotal: number }) => ({
            productId: item.productId,
            productName: item.productName,
            quantity: item.quantity,
            unitPrice: item.unitPrice,
            subtotal: item.subtotal,
          })),
        },
      },
      include: { saleItems: true },
    })

    // Deduct stock
    for (const item of items) {
      await db.product.update({
        where: { id: item.productId },
        data: { stock: { decrement: item.quantity } },
      })
    }

    return NextResponse.json(sale, { status: 201 })
  } catch (error) {
    console.error('Error creating sale:', error)
    return NextResponse.json({ error: 'Erreur lors de l\'enregistrement de la vente' }, { status: 500 })
  }
}
