// ============================================================
// InboundPage.tsx — Enrichissement leads entrants Clay-style
// ============================================================
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Copy, CheckCheck, Trash2, ArrowDownToLine } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '../api/client';
import { PageHeader } from '../components/layout/AppShell';
import { EmptyState } from '../components/ui/EmptyState';

interface InboundSource {
  id: string; name: string; token: string; webhook_url: string;
  source_type: string; is_active: boolean; leads_count: number; created_at: string;
}

export function InboundPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: '', source_type: 'webhook',
    field_mapping: { email: 'email', company_name: 'company', siren: 'siren', phone: 'phone' },
    auto_enrich: true,
  });

  const { data: sources, isLoading } = useQuery<InboundSource[]>({
    queryKey: ['inbound-sources'],
    queryFn: async () => { const { data } = await apiClient.get('/inbound'); return data; },
  });

  const createMutation = useMutation({
    mutationFn: (body: typeof form) => apiClient.post('/inbound', body),
    onSuccess: () => { toast.success('Source inbound créée'); qc.invalidateQueries({ queryKey: ['inbound-sources'] }); setShowForm(false); },
  });

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(`${window.location.origin}${text}`);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <>
      <PageHeader title="Inbound Enrichment" description="Enrichissez automatiquement vos leads entrants (Typeform, HubSpot forms...)"
        actions={<button onClick={() => setShowForm(v => !v)} className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"><Plus className="w-4 h-4" /> Nouvelle source</button>} />
      <div className="p-6 space-y-4">
        {showForm && (
          <div className="bg-white rounded-lg border p-4 space-y-3">
            <h3 className="font-semibold">Nouvelle source inbound</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1">Nom</label>
                <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Formulaire contact site web" className="w-full px-3 py-2 text-sm border rounded" />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Type</label>
                <select value={form.source_type} onChange={e => setForm(f => ({ ...f, source_type: e.target.value }))} className="w-full px-3 py-2 text-sm border rounded">
                  <option value="webhook">Webhook générique</option>
                  <option value="typeform">Typeform</option>
                  <option value="hubspot">HubSpot form</option>
                </select>
              </div>
            </div>
            <div>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={form.auto_enrich} onChange={e => setForm(f => ({ ...f, auto_enrich: e.target.checked }))} />
                Enrichir automatiquement via INSEE si SIREN fourni
              </label>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowForm(false)} className="px-4 py-2 border rounded text-sm">Annuler</button>
              <button onClick={() => createMutation.mutate(form)} disabled={!form.name} className="px-4 py-2 bg-blue-600 text-white rounded text-sm disabled:opacity-50">Créer</button>
            </div>
          </div>
        )}

        {isLoading && <p className="text-sm text-gray-500">Chargement…</p>}
        {!isLoading && !sources?.length && <EmptyState title="Aucune source inbound" description="Créez une source pour recevoir et enrichir des leads automatiquement." icon={<ArrowDownToLine className="w-12 h-12" />} />}

        {sources?.map(src => (
          <div key={src.id} className="bg-white rounded-lg border p-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{src.name}</span>
                  <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">{src.source_type}</span>
                  <span className="text-xs text-green-600 font-medium">{src.leads_count} leads</span>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                    POST {window.location.origin}{src.webhook_url}
                  </code>
                  <button onClick={() => copyToClipboard(src.webhook_url, src.id)}
                    className="text-gray-400 hover:text-blue-600 transition">
                    {copied === src.id ? <CheckCheck className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

export default InboundPage;
