import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useEffect, useState } from 'react'

export default function Settings() {
  const [siteName, setSiteName] = useState('')
  const [itemsPerPage, setItemsPerPage] = useState(12)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    try {
      const raw = localStorage.getItem('app_settings')
      if (raw) {
        const parsed = JSON.parse(raw)
        setSiteName(parsed.siteName || '')
        setItemsPerPage(parsed.itemsPerPage || 12)
      }
    } catch (e) {
      // ignore
    }
  }, [])

  const onSave = () => {
    const payload = { siteName, itemsPerPage }
    localStorage.setItem('app_settings', JSON.stringify(payload))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Configurações</h1>
      <Card>
        <CardHeader>
          <CardTitle>Preferências do Sistema</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 max-w-md">
            <div>
              <label className="block text-xs mb-1">Nome do site</label>
              <Input value={siteName} onChange={(e) => setSiteName((e.target as HTMLInputElement).value)} />
            </div>
            <div>
              <label className="block text-xs mb-1">Itens por página</label>
              <Input type="number" value={itemsPerPage} onChange={(e) => setItemsPerPage(Number((e.target as HTMLInputElement).value) || 1)} />
            </div>
            <div className="flex items-center gap-2">
              <Button onClick={onSave}>Salvar</Button>
              {saved && <span className="text-sm text-green-600">Salvo</span>}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}