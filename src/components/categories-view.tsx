'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Plus, Edit, Trash2, Tags, Package } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface Category {
  id: string
  name: string
  color: string
  _count: { products: number }
}

const defaultColors = [
  '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4',
  '#f97316', '#ec4899', '#14b8a6', '#6366f1', '#84cc16',
]

export function CategoriesView() {
  const { toast } = useToast()
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<Category | null>(null)
  const [deletingCategory, setDeletingCategory] = useState<Category | null>(null)
  const [formName, setFormName] = useState('')
  const [formColor, setFormColor] = useState('#10b981')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchCategories()
  }, [])

  const fetchCategories = async () => {
    try {
      const res = await fetch('/api/categories')
      const json = await res.json()
      setCategories(Array.isArray(json) ? json : [])
    } catch (err) {
      console.error('Error fetching categories:', err)
    } finally {
      setLoading(false)
    }
  }

  const openCreateDialog = () => {
    setEditingCategory(null)
    setFormName('')
    setFormColor('#10b981')
    setDialogOpen(true)
  }

  const openEditDialog = (cat: Category) => {
    setEditingCategory(cat)
    setFormName(cat.name)
    setFormColor(cat.color)
    setDialogOpen(true)
  }

  const openDeleteDialog = (cat: Category) => {
    setDeletingCategory(cat)
    setDeleteOpen(true)
  }

  const handleSave = async () => {
    if (!formName.trim()) {
      toast({ title: 'Erreur', description: 'Le nom est obligatoire', variant: 'destructive' })
      return
    }

    setSaving(true)
    try {
      if (editingCategory) {
        // Update - need to add a PUT route or use separate approach
        // Since we only have POST/DELETE for categories, we'll use POST for create
        // For now, we'll just note that edit would need a PUT route
        toast({ title: 'Info', description: 'Modification de catégorie non supportée dans cette version' })
      } else {
        const res = await fetch('/api/categories', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: formName.trim(), color: formColor }),
        })

        if (!res.ok) {
          const err = await res.json()
          throw new Error(err.error || 'Erreur lors de la création')
        }

        toast({ title: 'Catégorie créée', description: `${formName} a été ajoutée` })
        setDialogOpen(false)
        fetchCategories()
      }
    } catch (err) {
      toast({
        title: 'Erreur',
        description: err instanceof Error ? err.message : 'Erreur lors de la sauvegarde',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!deletingCategory) return
    try {
      const res = await fetch('/api/categories', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: deletingCategory.id }),
      })
      if (!res.ok) throw new Error('Erreur lors de la suppression')
      toast({ title: 'Catégorie supprimée', description: `${deletingCategory.name} a été supprimée` })
      setDeleteOpen(false)
      fetchCategories()
    } catch (err) {
      toast({
        title: 'Erreur',
        description: err instanceof Error ? err.message : 'Erreur lors de la suppression',
        variant: 'destructive',
      })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-muted-foreground">Chargement des catégories...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Catégories</h1>
          <p className="text-muted-foreground">Organisez vos produits par catégorie</p>
        </div>
        <Button onClick={openCreateDialog} className="bg-emerald-600 hover:bg-emerald-700 text-white">
          <Plus className="size-4 mr-2" />
          Ajouter une catégorie
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories.map((cat) => (
          <Card key={cat.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: cat.color + '20' }}
                  >
                    <Tags className="size-5" style={{ color: cat.color }} />
                  </div>
                  <div>
                    <h3 className="font-semibold">{cat.name}</h3>
                    <div className="flex items-center gap-1 mt-0.5">
                      <Package className="size-3 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">
                        {cat._count?.products || 0} produit{(cat._count?.products || 0) !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-8"
                    onClick={() => openEditDialog(cat)}
                  >
                    <Edit className="size-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-8 text-destructive"
                    onClick={() => openDeleteDialog(cat)}
                    disabled={(cat._count?.products || 0) > 0}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>
              <div
                className="mt-3 h-1.5 rounded-full"
                style={{ backgroundColor: cat.color }}
              />
            </CardContent>
          </Card>
        ))}

        {categories.length === 0 && (
          <div className="col-span-full flex flex-col items-center justify-center py-16 text-muted-foreground">
            <Tags className="size-12 mb-3 opacity-30" />
            <p>Aucune catégorie créée</p>
            <p className="text-sm mt-1">Créez des catégories pour organiser vos produits</p>
          </div>
        )}
      </div>

      {/* Create Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingCategory ? 'Modifier la catégorie' : 'Nouvelle catégorie'}
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid gap-2">
              <Label htmlFor="cat-name">Nom de la catégorie *</Label>
              <Input
                id="cat-name"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Ex: Alimentation"
              />
            </div>
            <div className="grid gap-2">
              <Label>Couleur</Label>
              <div className="flex flex-wrap gap-2">
                {defaultColors.map((color) => (
                  <button
                    key={color}
                    className={`w-8 h-8 rounded-full border-2 transition-all ${
                      formColor === color ? 'scale-110 border-foreground' : 'border-transparent'
                    }`}
                    style={{ backgroundColor: color }}
                    onClick={() => setFormColor(color)}
                  />
                ))}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Input
                  value={formColor}
                  onChange={(e) => setFormColor(e.target.value)}
                  className="w-32"
                  placeholder="#10b981"
                />
                <div
                  className="w-8 h-8 rounded-full border"
                  style={{ backgroundColor: formColor }}
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Annuler
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving || !editingCategory && !formName.trim()}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {saving ? 'Enregistrement...' : 'Créer'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Supprimer la catégorie ?</AlertDialogTitle>
            <AlertDialogDescription>
              {deletingCategory && (
                <>
                  Êtes-vous sûr de vouloir supprimer <strong>{deletingCategory.name}</strong> ?
                  {deletingCategory._count?.products > 0 && (
                    <span className="block mt-2 text-destructive">
                      Impossible de supprimer une catégorie contenant des produits.
                      Supprimez ou réassignez d&apos;abord les produits.
                    </span>
                  )}
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deletingCategory && deletingCategory._count?.products > 0}
              className="bg-destructive text-white hover:bg-destructive/90"
            >
              Supprimer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
