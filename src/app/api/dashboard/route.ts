import { db } from '@/lib/db'
import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    // Today's sales
    const todaySales = await db.sale.findMany({
      where: {
        createdAt: { gte: today, lt: tomorrow },
      },
    })

    const todayRevenue = todaySales.reduce((sum, s) => sum + s.total, 0)
    const todaySaleCount = todaySales.length

    // Active products count
    const productCount = await db.product.count({
      where: { isActive: true },
    })

    // Low stock alerts
    const lowStockProducts = await db.product.findMany({
      where: {
        isActive: true,
        stock: { lt: db.product.fields.minStock },
      },
    })

    // Top 5 best selling products
    const topProductsRaw = await db.saleItem.groupBy({
      by: ['productId', 'productName'],
      _sum: { quantity: true },
      orderBy: { _sum: { quantity: 'desc' } },
      take: 5,
    })

    const topProducts = topProductsRaw.map((p) => ({
      productName: p.productName,
      totalSold: p._sum.quantity || 0,
    }))

    // Recent 10 sales
    const recentSales = await db.sale.findMany({
      include: { saleItems: true },
      orderBy: { createdAt: 'desc' },
      take: 10,
    })

    // Weekly sales data
    const weekAgo = new Date()
    weekAgo.setDate(weekAgo.getDate() - 7)
    weekAgo.setHours(0, 0, 0, 0)

    const weekSales = await db.sale.findMany({
      where: { createdAt: { gte: weekAgo } },
    })

    const dailySales: Record<string, number> = {}
    for (let i = 6; i >= 0; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      d.setHours(0, 0, 0, 0)
      const key = d.toISOString().split('T')[0]
      dailySales[key] = 0
    }

    for (const sale of weekSales) {
      const key = sale.createdAt.toISOString().split('T')[0]
      if (dailySales[key] !== undefined) {
        dailySales[key] += sale.total
      }
    }

    const weeklyData = Object.entries(dailySales).map(([date, total]) => ({
      date,
      total,
    }))

    return NextResponse.json({
      todayRevenue,
      todaySaleCount,
      productCount,
      lowStockCount: lowStockProducts.length,
      lowStockProducts,
      topProducts,
      recentSales,
      weeklyData,
    })
  } catch (error) {
    console.error('Error fetching dashboard data:', error)
    return NextResponse.json({ error: 'Erreur lors de la récupération des données du tableau de bord' }, { status: 500 })
  }
}
