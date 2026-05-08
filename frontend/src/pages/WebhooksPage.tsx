import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, TestTube2, Webhook } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '../api/client';
import { PageHeader } from '../components/layout/AppShell';
import { EmptyState } from '../components/ui/EmptyState';

const EVENTS = [
  'prospect.created', 'prospect.enriched', 'prospect.stage_changed',
  'prospect.deleted', 'activity.created',
];

export default function WebhooksPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', url: '', secret: '', events: [] as string[] });

  const { data, isLoading } = useQuery({
    queryKey: ['webhooks'],
    queryFn: async () => { const { data } = await apiClient.get('/webhooks'); return data; },
  });

  const createMutation = useMutation({
    mutationFn: (body: typeof form) => apiClient.post('/webhooks', body),
    onSuccess: () => { toast.success('Webhook créé'); qc.invalidateQueries({ queryKey: ['webhooks'] }); setShowForm(false); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/webhooks/${id}`),
    onSuccess: () => { toast.success('Webhook supprimé'); qc.invalidateQueries({ queryKey: ['webhooks'] }); },
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => apiClient.post(`/webhooks/${id}/test`),
    onSuccess: (data: any) => {
      if (data.data.success) toast.success('Test réussi ✓');
      else toast.error('Test échoué — vérifier l\'URL');
    },
  });

  return (
    <>
      <PageHeader
        title="Webhooks"
        description="Notifications sortantes vers Make, n8n, Zapier..."
        actions={
          <button onClick={() => setShowForm(v => !v)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
            <Plus className="w-4 h-4" /> Nouveau webhook
          </button>
        }
      />
      <div className="p-6 space-y-4">
        {showForm && (
          <div className="bg-white rounded-lg border p-4 space-y-3">
            <h3 className="font-semibold">Nouveau webhook</h3>
            <div className="grid grid-cols-2 gap-3">
              <input value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                placeholder="Nom" className="px-3 py-2 border rounded text-sm" />
              <input value={form.url} onChange={e => setForm({...form, url: e.target.value})}
                placeholder="https://hook.eu1.make.com/..." className="px-3 py-2 border rounded text-sm" />
              <input value={form.secret} onChange={e => setForm({...form, secret: e.target.value})}
                placeholder="Secret HMAC (optionnel)" className="px-3 py-2 border rounded text-sm" />
            </div>
            <div>
              <p className="text-xs font-medium mb-2">Événements</p>
              <div className="flex flex-wrap gap-2">
                {EVENTS.map(e => (
                  <label key={e} className="flex items-center gap-1.5 text-xs cursor-pointer">
                    <input type="checkbox" checked={form.events.includes(e)}
                      onChange={ev => setForm({...form, events: ev.target.checked
                        ? [...form.events, e] : form.events.filter(x => x !== e)})} />
                    {e}
                  </label>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowForm(false)} className="px-4 py-2 border rounded text-sm">Annuler</button>
              <button onClick={() => createMutation.mutate(form)}
                className="px-4 py-2 bg-blue-600 text-white rounded text-sm">Créer</button>
            </div>
          </div>
        )}

        {isLoading && <p className="text-gray-500 text-sm">Chargement…</p>}

        {!isLoading && (!data || data.length === 0) && (
          <EmptyState title="Aucun webhook configuré"
            description="Connectez Make, n8n, Zapier ou votre propre endpoint."
            icon={<Webhook className="w-12 h-12" />} />
        )}

        {data && data.map((wh: any) => (
          <div key={wh.id} className="bg-white rounded-lg border p-4 flex items-center justify-between">
            <div>
              <div className="font-medium text-sm">{wh.name}</div>
              <div className="text-xs text-gray-500 font-mono truncate max-w-md">{wh.url}</div>
              <div className="flex gap-1 mt-1">
                {wh.events.map((e: string) => (
                  <span key={e} className="text-xs px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded">{e}</span>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="text-green-600">✓ {wh.success_count}</span>
              <span className="text-red-500">✗ {wh.fail_count}</span>
              <button onClick={() => testMutation.mutate(wh.id)}
                className="flex items-center gap-1 px-2.5 py-1 border rounded hover:bg-gray-50">
                <TestTube2 className="w-3.5 h-3.5" /> Test
              </button>
              <button onClick={() => deleteMutation.mutate(wh.id)}
                className="p-1.5 text-gray-400 hover:text-red-500">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
