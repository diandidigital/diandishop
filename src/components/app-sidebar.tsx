'use client'

import {
  BarChart3,
  ShoppingCart,
  Package,
  History,
  Tags,
  Store,
} from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar'

export type AppView = 'dashboard' | 'pos' | 'products' | 'sales' | 'categories'

interface AppSidebarProps {
  activeView: AppView
  onViewChange: (view: AppView) => void
}

const navItems: { view: AppView; label: string; icon: React.ReactNode }[] = [
  { view: 'dashboard', label: 'Tableau de bord', icon: <BarChart3 className="size-4" /> },
  { view: 'pos', label: 'Caisse (POS)', icon: <ShoppingCart className="size-4" /> },
  { view: 'products', label: 'Produits', icon: <Package className="size-4" /> },
  { view: 'sales', label: 'Historique des ventes', icon: <History className="size-4" /> },
  { view: 'categories', label: 'Catégories', icon: <Tags className="size-4" /> },
]

export function AppSidebar({ activeView, onViewChange }: AppSidebarProps) {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-4">
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Store className="size-5" />
          </div>
          <span className="text-lg font-bold text-sidebar-foreground group-data-[collapsible=icon]:hidden">
            DiandiShop
          </span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu principal</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.view}>
                  <SidebarMenuButton
                    isActive={activeView === item.view}
                    onClick={() => onViewChange(item.view)}
                    tooltip={item.label}
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="px-4 py-3">
        <div className="group-data-[collapsible=icon]:hidden">
          <p className="text-xs font-semibold text-sidebar-foreground/70">DiandiDigital.tech</p>
          <p className="text-xs text-sidebar-foreground/50">v1.0</p>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
