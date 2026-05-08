import { Users, TrendingUp, Wallet, Puzzle, RefreshCw } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useDashboardStats } from '../hooks/useDashboard';
import { PageHeader } from '../components/layout/AppShell';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { formatCurrency, formatNumber, formatPercent } from '../lib/utils';

export default function Dashboard() {
  const { data, isLoading, error, refetch, isRefetching } = useDashboardStats();

  if (isLoading) {
    return (
      <>
        <PageHeader title="Dashboard" description="Vue d'ensemble de votre activité commerciale" />
        <div className="p-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-28" />)}
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <PageHeader title="Dashboard" />
        <div className="p-6">
          <EmptyState
            title="Impossible de charger le dashboard"
            description="Vérifiez la connexion au backend ou consultez les logs."
            action={
              <button onClick={() => refetch()} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                Réessayer
              </button>
            }
          />
        </div>
      </>
    );
  }

  const kpi = data!.kpi;
  const distribution = data!.distribution;

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Vue d'ensemble de votre activité commerciale"
        actions={
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="flex items-center gap-2 px-3 py-1.5 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefetching ? 'animate-spin' : ''}`} />
            Actualiser
          </button>
        }
      />

      <div className="p-6 space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            label="Prospects"
            value={formatNumber(kpi.total_prospects)}
            icon={<Users className="w-5 h-5 text-blue-600" />}
            color="blue"
          />
          <KpiCard
            label="Taux de conversion"
            value={formatPercent(kpi.conversion_rate)}
            icon={<TrendingUp className="w-5 h-5 text-green-600" />}
            color="green"
          />
          <KpiCard
            label="CA prévisionnel"
            value={formatCurrency(kpi.estimated_revenue)}
            icon={<Wallet className="w-5 h-5 text-purple-600" />}
            color="purple"
          />
          <KpiCard
            label="Plugins actifs"
            value={String(kpi.active_plugins)}
            icon={<Puzzle className="w-5 h-5 text-orange-600" />}
            color="orange"
          />
        </div>

        {/* Distribution */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-1">Répartition par étape</h2>
          <p className="text-sm text-gray-500 mb-4">Pipeline commercial en temps réel</p>

          {distribution.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">Aucune donnée à afficher</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={distribution}>
                <XAxis dataKey="stage_name" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: 4,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {distribution.map((entry) => (
                    <Cell key={entry.stage_id} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <p className="text-xs text-gray-400 text-right">
          Dernière mise à jour : {new Date(data!.last_updated).toLocaleString('fr-FR')}
        </p>
      </div>
    </>
  );
}

function KpiCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  color?: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <div className="flex items-start justify-between mb-2">
        <p className="text-sm text-gray-500">{label}</p>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
