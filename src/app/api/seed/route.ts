import { db } from '@/lib/db'
import { NextResponse } from 'next/server'

export async function POST() {
  try {
    // Check if data already exists
    const existingProducts = await db.product.count()
    if (existingProducts > 0) {
      return NextResponse.json({ message: 'Les données de démo existent déjà', seeded: false })
    }

    // Create categories
    const categories = await Promise.all([
      db.category.create({ data: { name: 'Alimentation', color: '#10b981' } }),
      db.category.create({ data: { name: 'Boissons', color: '#06b6d4' } }),
      db.category.create({ data: { name: 'Produits d\'entretien', color: '#f59e0b' } }),
      db.category.create({ data: { name: 'Cosmétiques', color: '#ec4899' } }),
      db.category.create({ data: { name: 'Divers', color: '#8b5cf6' } }),
    ])

    const catMap: Record<string, string> = {}
    categories.forEach((c) => { catMap[c.name] = c.id })

    // Create products
    const productsData = [
      { name: 'Riz 25kg', price: 15000, costPrice: 13000, stock: 20, minStock: 5, categoryId: catMap['Alimentation'] },
      { name: 'Huile de palme 1L', price: 1500, costPrice: 1100, stock: 30, minStock: 10, categoryId: catMap['Alimentation'] },
      { name: 'Sucre 1kg', price: 800, costPrice: 650, stock: 50, minStock: 10, categoryId: catMap['Alimentation'] },
      { name: 'Lait浓缩 Nido 400g', price: 2200, costPrice: 1800, stock: 25, minStock: 8, categoryId: catMap['Alimentation'] },
      { name: 'Pâtes Spaghetti 500g', price: 500, costPrice: 350, stock: 40, minStock: 10, categoryId: catMap['Alimentation'] },
      { name: 'Concentré de tomate 400g', price: 350, costPrice: 250, stock: 35, minStock: 10, categoryId: catMap['Alimentation'] },
      { name: 'Savon Marseille 400g', price: 500, costPrice: 350, stock: 45, minStock: 10, categoryId: catMap['Produits d\'entretien'] },
      { name: 'Dettol 500ml', price: 1800, costPrice: 1400, stock: 15, minStock: 5, categoryId: catMap['Produits d\'entretien'] },
      { name: 'Eau de Javel 1L', price: 400, costPrice: 250, stock: 30, minStock: 8, categoryId: catMap['Produits d\'entretien'] },
      { name: 'Lessive Omo 500g', price: 1200, costPrice: 900, stock: 20, minStock: 5, categoryId: catMap['Produits d\'entretien'] },
      { name: 'Coca-Cola 33cl', price: 300, costPrice: 200, stock: 100, minStock: 20, categoryId: catMap['Boissons'] },
      { name: 'Eau Vitale 1.5L', price: 350, costPrice: 200, stock: 80, minStock: 20, categoryId: catMap['Boissons'] },
      { name: 'Bissap 1L', price: 500, costPrice: 300, stock: 25, minStock: 8, categoryId: catMap['Boissons'] },
      { name: 'Gingembre 1L', price: 500, costPrice: 300, stock: 20, minStock: 8, categoryId: catMap['Boissons'] },
      { name: 'Crème Nivea 250ml', price: 2500, costPrice: 2000, stock: 15, minStock: 5, categoryId: catMap['Cosmétiques'] },
      { name: 'Pomade DP 50g', price: 1500, costPrice: 1000, stock: 18, minStock: 5, categoryId: catMap['Cosmétiques'] },
      { name: 'Savon Dove 135g', price: 800, costPrice: 550, stock: 22, minStock: 5, categoryId: catMap['Cosmétiques'] },
      { name: 'Sachets plastique (lot)', price: 250, costPrice: 150, stock: 3, minStock: 10, categoryId: catMap['Divers'] },
      { name: 'Allumettes (lot)', price: 100, costPrice: 50, stock: 50, minStock: 15, categoryId: catMap['Divers'] },
      { name: 'Bougies (lot de 6)', price: 500, costPrice: 300, stock: 12, minStock: 5, categoryId: catMap['Divers'] },
    ]

    const products = await Promise.all(
      productsData.map((p) =>
        db.product.create({ data: p })
      )
    )

    const prodMap: Record<string, { id: string; costPrice: number; price: number }> = {}
    products.forEach((p) => { prodMap[p.name] = { id: p.id, costPrice: p.costPrice, price: p.price } })

    // Create sample sales for the past few days
    const now = new Date()
    const salesData = [
      {
        daysAgo: 6,
        items: [
          { name: 'Riz 25kg', qty: 2 },
          { name: 'Huile de palme 1L', qty: 3 },
        ],
        payment: 'cash',
      },
      {
        daysAgo: 5,
        items: [
          { name: 'Coca-Cola 33cl', qty: 6 },
          { name: 'Eau Vitale 1.5L', qty: 4 },
          { name: 'Bissap 1L', qty: 2 },
        ],
        payment: 'cash',
      },
      {
        daysAgo: 4,
        items: [
          { name: 'Savon Marseille 400g', qty: 3 },
          { name: 'Dettol 500ml', qty: 1 },
          { name: 'Lessive Omo 500g', qty: 2 },
        ],
        payment: 'mobile',
      },
      {
        daysAgo: 3,
        items: [
          { name: 'Sucre 1kg', qty: 4 },
          { name: 'Lait浓缩 Nido 400g', qty: 2 },
          { name: 'Pâtes Spaghetti 500g', qty: 3 },
        ],
        payment: 'cash',
      },
      {
        daysAgo: 2,
        items: [
          { name: 'Crème Nivea 250ml', qty: 1 },
          { name: 'Pomade DP 50g', qty: 2 },
          { name: 'Savon Dove 135g', qty: 3 },
        ],
        payment: 'mobile',
      },
      {
        daysAgo: 1,
        items: [
          { name: 'Riz 25kg', qty: 1 },
          { name: 'Concentré de tomate 400g', qty: 4 },
          { name: 'Huile de palme 1L', qty: 2 },
        ],
        payment: 'cash',
      },
      {
        daysAgo: 0,
        items: [
          { name: 'Eau Vitale 1.5L', qty: 3 },
          { name: 'Gingembre 1L', qty: 2 },
          { name: 'Allumettes (lot)', qty: 5 },
        ],
        payment: 'cash',
      },
    ]

    for (const sale of salesData) {
      const saleDate = new Date(now)
      saleDate.setDate(saleDate.getDate() - sale.daysAgo)
      saleDate.setHours(9 + Math.floor(Math.random() * 10), Math.floor(Math.random() * 60))

      const saleItems = sale.items.map((item) => {
        const prod = prodMap[item.name]
        return {
          productId: prod.id,
          productName: item.name,
          quantity: item.qty,
          unitPrice: prod.price,
          costPrice: prod.costPrice,
          subtotal: prod.price * item.qty,
        }
      })

      const total = saleItems.reduce((sum, item) => sum + item.subtotal, 0)
      const profit = saleItems.reduce((sum, item) => sum + (item.quantity * (item.unitPrice - item.costPrice)), 0)

      await db.sale.create({
        data: {
          total,
          profit,
          paymentMethod: sale.payment,
          createdAt: saleDate,
          saleItems: {
            create: saleItems.map((item) => ({
              productId: item.productId,
              productName: item.productName,
              quantity: item.quantity,
              unitPrice: item.unitPrice,
              subtotal: item.subtotal,
            })),
          },
        },
      })

      // Deduct stock
      for (const item of sale.items) {
        const prod = prodMap[item.name]
        await db.product.update({
          where: { id: prod.id },
          data: { stock: { decrement: item.qty } },
        })
      }
    }

    return NextResponse.json({
      message: 'Données de démonstration insérées avec succès',
      seeded: true,
      categories: categories.length,
      products: products.length,
      sales: salesData.length,
    })
  } catch (error) {
    console.error('Error seeding data:', error)
    return NextResponse.json({ error: 'Erreur lors de l\'insertion des données' }, { status: 500 })
  }
}
