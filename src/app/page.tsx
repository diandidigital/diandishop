'use client'

import { useState } from 'react'
import { AppSidebar, type AppView } from '@/components/app-sidebar'
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { DashboardView } from '@/components/dashboard-view'
import { PosView } from '@/components/pos-view'
import { ProductsView } from '@/components/products-view'
import { SalesView } from '@/components/sales-view'
import { CategoriesView } from '@/components/categories-view'
import { Separator } from '@/components/ui/separator'

export default function Home() {
  const [activeView, setActiveView] = useState<AppView>('dashboard')

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardView />
      case 'pos':
        return <PosView />
      case 'products':
        return <ProductsView />
      case 'sales':
        return <SalesView />
      case 'categories':
        return <CategoriesView />
      default:
        return <DashboardView />
    }
  }

  return (
    <SidebarProvider>
      <AppSidebar activeView={activeView} onViewChange={setActiveView} />
      <SidebarInset>
        <header className="flex h-12 items-center gap-2 border-b px-4">
          <SidebarTrigger />
          <Separator orientation="vertical" className="h-6" />
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">
              {activeView === 'dashboard' && 'Tableau de bord'}
              {activeView === 'pos' && 'Caisse'}
              {activeView === 'products' && 'Produits'}
              {activeView === 'sales' && 'Historique des ventes'}
              {activeView === 'categories' && 'Catégories'}
            </span>
          </div>
        </header>
        <main className="flex-1 p-4 md:p-6 overflow-auto">
          {renderView()}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
