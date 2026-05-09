import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, Bell, CheckCheck, Zap, Info } from 'lucide-react';
import { apiClient } from '../api/client';
import { PageHeader } from '../components/layout/AppShell';

const SIGNAL_ICONS: Record<string, React.ReactNode> = {
  bodacc_procedure: <AlertTriangle className="w-4 h-4 text-red-500" />,
  bodacc_creation: <Zap className="w-4 h-4 text-green-500" />,
  hot_no_contact: <Bell className="w-4 h-4 text-orange-500" />,
  no_website: <Info className="w-4 h-4 text-blue-500" />,
  default: <Bell className="w-4 h-4 text-gray-500" />,
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'border-l-4 border-red-500 bg-red-50',
  warning: 'border-l-4 border-orange-400 bg-orange-50',
  info: 'border-l-4 border-blue-400 bg-blue-50',
};

interface Signal {
  id: string; prospect_id: string; prospect_name: string;
  type: string; title: string; description: string | null;
  source: string; severity: string; is_read: boolean;
  signal_date: string | null; created_at: string;
}

interface Summary { total: number; unread: number; critical_unread: number; last_7_days: number; }

export default function SignalsPage() {
  const qc = useQueryClient();

  const { data: summary } = useQuery<Summary>({
    queryKey: ['signals-summary'],
    queryFn: async () => { const { data } = await apiClient.get('/signals/summary'); return data; },
    refetchInterval: 30_000,
  });

  const { data: signals, isLoading } = useQuery<Signal[]>({
    queryKey: ['signals'],
    queryFn: async () => { const { data } = await apiClient.get('/signals?limit=100'); return data; },
    refetchInterval: 30_000,
  });

  const markReadMutation = useMutation({
    mutationFn: (ids: string[]) => apiClient.post('/signals/mark-read', ids),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['signals', 'signals-summary'] }),
  });

  const unread = signals?.filter(s => !s.is_read) || [];

  return (
    <>
      <PageHeader
        title="Signals & Intent"
        description="Détection automatique d'événements business sur vos prospects"
        actions={
          unread.length > 0 ? (
            <button onClick={() => markReadMutation.mutate(unread.map(s => s.id))}
              className="flex items-center gap-2 px-3 py-1.5 text-sm border rounded hover:bg-gray-50">
              <CheckCheck className="w-4 h-4" /> Tout marquer lu
            </button>
          ) : null
        }
      />
      <div className="p-6 space-y-4">
        {/* KPI cards */}
        {summary && (
          <div className="grid grid-cols-4 gap-4">
            <KpiCard label="Total signaux" value={summary.total} icon="📊" />
            <KpiCard label="Non lus" value={summary.unread} icon="🔔" highlight={summary.unread > 0} />
            <KpiCard label="Critiques" value={summary.critical_unread} icon="⚠️" highlight={summary.critical_unread > 0} />
            <KpiCard label="7 derniers jours" value={summary.last_7_days} icon="📅" />
          </div>
        )}

        {/* Feed de signaux */}
        {isLoading && <p className="text-gray-500 text-sm">Chargement des signaux…</p>}

        {signals && signals.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Aucun signal détecté</p>
            <p className="text-sm mt-1">Lancez la détection sur vos prospects depuis la page Prospects</p>
          </div>
        )}

        <div className="space-y-2">
          {signals?.map((signal) => (
            <div
              key={signal.id}
              className={`rounded-lg p-4 transition cursor-pointer ${
                SEVERITY_COLORS[signal.severity] || SEVERITY_COLORS.info
              } ${!signal.is_read ? 'opacity-100' : 'opacity-60'}`}
              onClick={() => !signal.is_read && markReadMutation.mutate([signal.id])}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex-shrink-0">
                    {SIGNAL_ICONS[signal.type] || SIGNAL_ICONS.default}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{signal.title}</span>
                      {!signal.is_read && (
                        <span className="w-2 h-2 rounded-full bg-blue-600 flex-shrink-0" />
                      )}
                    </div>
                    <div className="text-xs text-gray-600 mt-0.5">
                      <span className="font-medium">{signal.prospect_name}</span>
                      {signal.description && <span className="ml-2">{signal.description}</span>}
                    </div>
                  </div>
                </div>
                <div className="text-xs text-gray-400 flex-shrink-0 ml-4">
                  {new Date(signal.created_at).toLocaleString('fr-FR', {
                    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function KpiCard({ label, value, icon, highlight }: { label: string; value: number; icon: string; highlight?: boolean }) {
  return (
    <div className={`bg-white rounded-lg border p-4 ${highlight ? 'border-orange-300' : ''}`}>
      <div className="text-2xl mb-1">{icon}</div>
      <div className={`text-2xl font-bold ${highlight ? 'text-orange-600' : 'text-gray-900'}`}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}
