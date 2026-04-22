# DiandiShop - Worklog

## Date: 2026-04-21

### Étape 1: Schéma Prisma ✅
- Remplacé les modèles User et Post par Category, Product, Sale, SaleItem
- Relations correctes entre modèles (Category → Product, Sale → SaleItem → Product)
- Soft delete sur Product (isActive)
- `bun run db:push` et `bun run db:generate` réussis

### Étape 2: Routes API ✅
- `/api/products` - GET (recherche + filtre catégorie), POST (création)
- `/api/products/[id]` - GET, PUT, DELETE (soft delete)
- `/api/categories` - GET, POST, DELETE
- `/api/sales` - GET (filtre date + limit), POST (création + déduction stock)
- `/api/dashboard` - Stats du jour, top produits, ventes récentes, données hebdomadaires
- `/api/seed` - Insertion données de démonstration

### Étape 3: Thème et Layout ✅
- globals.css: thème vert émeraude (oklch) pour primary, sidebar, charts
- layout.tsx: titre "DiandiShop", lang="fr"
- Aucune couleur bleu/indigo

### Étape 4: Composants ✅
- `app-sidebar.tsx` - Navigation avec Store icon, 5 onglets, sidebar footer
- `dashboard-view.tsx` - 4 cartes stats, graphique recharts BarChart, top produits, ventes récentes, alertes stock
- `pos-view.tsx` - Grille produits + panier, recherche/filtre catégorie, +/- quantités, encaissement avec Espèces/Mobile Money, calcul monnaie, dialog confirmation
- `products-view.tsx` - Tableau avec recherche/filtre, CRUD dialog, indicateurs stock (vert/orange/rouge)
- `sales-view.tsx` - Historique avec filtre date, résumé (nb ventes, total, bénéfice), détail vente
- `categories-view.tsx` - Cartes catégories, sélection couleur, ajout/suppression

### Étape 5: Page principale ✅
- Single-page app avec SidebarProvider + state React pour navigation
- Header avec SidebarTrigger + titre de la vue active

### Étape 6: Données de démonstration ✅
- 5 catégories: Alimentation, Boissons, Produits d'entretien, Cosmétiques, Divers
- 20 produits avec prix réalistes en FCFA
- 7 ventes sur 7 jours avec stock déduit

### Vérification ✅
- ESLint: 0 erreurs
- Dev log: pas d'erreurs, compilation réussie
- Seed API: données insérées avec succès
