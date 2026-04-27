import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useDashboard, type ProductItem } from '@/hooks/use-dashboard';
import { useEffect, useMemo, useState } from 'react';

export default function Users() {
  const [region, setRegion] = useState('all');
  const [category, setCategory] = useState('all');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 12;
  const [blockedUsers, setBlockedUsers] = useState<Set<string>>(new Set());

  const toggleBlock = (client: string) => {
    setBlockedUsers((prev) => {
      const next = new Set(prev);
      if (next.has(client)) next.delete(client);
      else next.add(client);
      return next;
    });
  };
  const [edits, setEdits] = useState<Record<string, Partial<ProductItem>>>({})
  const [editing, setEditing] = useState<ProductItem | null>(null)

  useEffect(() => {
    try {
      const rawBlocked = localStorage.getItem('blocked_users')
      if (rawBlocked) setBlockedUsers(new Set(JSON.parse(rawBlocked)))
      const rawEdits = localStorage.getItem('user_edits')
      if (rawEdits) setEdits(JSON.parse(rawEdits))
    } catch (e) {
      // ignore
    }
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem('blocked_users', JSON.stringify(Array.from(blockedUsers)))
    } catch (e) { }
  }, [blockedUsers])

  useEffect(() => {
    try {
      localStorage.setItem('user_edits', JSON.stringify(edits))
    } catch (e) { }
  }, [edits])

  const saveEdit = (client: string, patch: Partial<ProductItem>) => {
    setEdits(prev => ({ ...prev, [client]: { ...(prev[client] || {}), ...patch } }))
    setEditing(null)
  }

  // Filtros para buscar todos os produtos e extrair clientes únicos
  const filters = useMemo(() => ({ period: 'all', category, region, status: 'all', search }), [category, region, search]);
  const tableParams = useMemo(() => ({ page: 1, pageSize: 50, sortBy: 'client', sortOrder: 'asc' as 'asc' | 'desc' }), [filters]);
  const { products, filterOptions, isLoading, error } = useDashboard(filters, tableParams);

  // Extrair clientes únicos e status mais recente
  const users = useMemo(() => {
    if (!products) return [];
    const map = new Map<string, ProductItem>();
    for (const item of products.items) {
      // Mantém o registro mais recente por data para cada cliente
      if (!map.has(item.client) || map.get(item.client)!.date < item.date) {
        map.set(item.client, item);
      }
    }

    let arr = Array.from(map.values());
    // Filtro de busca
    if (search) {
      const s = search.toLowerCase();
      arr = arr.filter(u => u.client.toLowerCase().includes(s));
    }
    // Paginação
    const start = (page - 1) * pageSize;
    return arr.slice(start, start + pageSize);
  }, [products, search, page, pageSize]);

  const totalUsers = useMemo(() => {
    if (!products) return 0;
    const set = new Set(products.items.map(i => i.client));
    return set.size;
  }, [products]);

  const totalPages = Math.ceil(totalUsers / pageSize) || 1;

  const resetFilters = () => {
    setRegion('all');
    setCategory('all');
    setSearch('');
    setPage(1);
  };

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold mb-4">Usuários</h1>
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="block text-xs mb-1">Categoria</label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Categoria" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {filterOptions?.categories.map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-xs mb-1">Região</label>
              <Select value={region} onValueChange={setRegion}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Região" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {filterOptions?.regions.map((r) => (
                    <SelectItem key={r} value={r}>{r}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-xs mb-1">Busca</label>
              <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar usuário..." className="w-48" />
            </div>
            <Button variant="ghost" onClick={resetFilters}>Limpar</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Lista de Usuários</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-12 text-center text-muted-foreground">Carregando...</div>
          ) : error ? (
            <div className="py-12 text-center text-destructive">Erro ao carregar usuários.</div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead>Categoria</TableHead>
                    <TableHead>Região</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Ações</TableHead>
                    <TableHead>Última Atividade</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => {
                    const merged = { ...user, ...(edits[user.client] || {}) }
                    return (
                      <TableRow key={user.client}>
                        <TableCell>{merged.client}</TableCell>
                        <TableCell>{merged.category}</TableCell>
                        <TableCell>{merged.region}</TableCell>
                        <TableCell>
                          <Badge>{blockedUsers.has(user.client) ? 'Blocked' : merged.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button size="sm" variant="ghost">Editar</Button>
                              </DialogTrigger>
                              <DialogContent>
                                <DialogHeader>
                                  <DialogTitle>Editar usuário</DialogTitle>
                                </DialogHeader>
                                <div className="space-y-3 mt-2">
                                  <div>
                                    <Label>Categoria</Label>
                                    <Input value={merged.category} onChange={e => saveEdit(user.client, { category: (e.target as HTMLInputElement).value })} />
                                  </div>
                                  <div>
                                    <Label>Região</Label>
                                    <Input value={merged.region} onChange={e => saveEdit(user.client, { region: (e.target as HTMLInputElement).value })} />
                                  </div>
                                  <div>
                                    <Label>Status</Label>
                                    <Input value={merged.status} onChange={e => saveEdit(user.client, { status: (e.target as HTMLInputElement).value })} />
                                  </div>
                                </div>
                                <DialogFooter>
                                  <DialogClose asChild>
                                    <Button variant="ghost">Fechar</Button>
                                  </DialogClose>
                                </DialogFooter>
                              </DialogContent>
                            </Dialog>
                            <Button size="sm" variant="destructive" onClick={() => toggleBlock(user.client)}>{blockedUsers.has(user.client) ? 'Desbloquear' : 'Bloquear'}</Button>
                          </div>
                        </TableCell>
                        <TableCell>{merged.date}</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
              <div className="flex justify-between items-center mt-4">
                <span className="text-xs text-muted-foreground">
                  Página {page} de {totalPages} — {totalUsers} usuários
                </span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Anterior</Button>
                  <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>Próxima</Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}