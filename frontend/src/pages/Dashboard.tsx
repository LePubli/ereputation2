import { useRef } from 'react';
import { Link } from 'react-router-dom';
import { Users, TrendingUp, Wallet, Zap, RefreshCw, ArrowUpRight, Bell, Bot, ChevronRight, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LineChart, Line, CartesianGrid, AreaChart, Area } from 'recharts';
import { useDashboardStats } from '../hooks/useDashboard';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { PageHeader } from '../components/ui/PageHeader';
import { formatCurrency, formatNumber, formatPercent } from '../lib/utils';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', boxShadow: 'var(--s-lg)' }}>
      <p style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ fontSize: 12, color: p.color }}>{p.value} prospects</p>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const { data, isLoading, refetch, isRefetching } = useDashboardStats();
  const { data: signalsSummary } = useQuery({
    queryKey: ['signals-summary'],
    queryFn: async () => { try { const { data } = await apiClient.get('/signals/summary'); return data; } catch { return null; } },
    staleTime: 30_000,
  });

  if (isLoading) return <DashboardSkeleton />;

  const kpi = data?.kpi;
  const dist = data?.distribution || [];

  // Simule une courbe de croissance depuis la distribution
  const trendData = dist.map((d: any, i: number) => ({
    name: d.stage_name,
    value: d.count,
    fill: d.color,
  }));

  return (
    <div className="app-page">
      <PageHeader
        title="Dashboard"
        actions={
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary btn-sm" onClick={() => refetch()} disabled={isRefetching}>
              <RefreshCw size={13} className={isRefetching ? 'animate-spin' : ''} />
              Actualiser
            </button>
            <Link to="/table" className="btn btn-primary btn-sm">
              <span>Ouvrir Spreadsheet</span>
              <ArrowUpRight size={13} />
            </Link>
          </div>
        }
      />

      <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* KPI Row */}
        <div className="kpi-grid kpi-grid-4">
          <KpiCard
            label="Total prospects"
            value={formatNumber(kpi?.total_prospects)}
            sub="dans la base"
            icon={<Users size={16} />}
            cls="kpi-purple"
            iconCls="kpi-icon-purple"
            trend={kpi?.total_prospects > 0 ? '+' + kpi.total_prospects : undefined}
          />
          <KpiCard
            label="Taux de conversion"
            value={formatPercent(kpi?.conversion_rate)}
            sub="prospects gagnés"
            icon={<TrendingUp size={16} />}
            cls="kpi-green"
            iconCls="kpi-icon-green"
          />
          <KpiCard
            label="CA prévisionnel"
            value={formatCurrency(kpi?.estimated_revenue)}
            sub="pipeline actif"
            icon={<Wallet size={16} />}
            cls="kpi-blue"
            iconCls="kpi-icon-blue"
          />
          <KpiCard
            label="Plugins actifs"
            value={String(kpi?.active_plugins || 0)}
            sub="modules en ligne"
            icon={<Zap size={16} />}
            cls="kpi-orange"
            iconCls="kpi-icon-orange"
          />
        </div>

        {/* Charts + Activity */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 340px', gap: 16 }}>
          {/* Pipeline distribution */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Pipeline commercial</div>
                <div className="card-sub">Répartition par étape</div>
              </div>
            </div>
            <div style={{ padding: '16px 16px 8px' }}>
              {dist.length === 0 ? (
                <div className="empty-state" style={{ padding: 32 }}>
                  <div className="empty-title">Aucune donnée</div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={trendData} barSize={28} barGap={4}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--tx-muted)' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: 'var(--tx-muted)' }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--bg-subtle)' }} />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {trendData.map((entry: any) => (
                        <Cell key={entry.name} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Scores distribution */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Qualité du pipeline</div>
                <div className="card-sub">Score de propension moyen</div>
              </div>
            </div>
            <div style={{ padding: '16px' }}>
              {['HOT', 'WARM', 'COLD'].map(cat => {
                const count = dist.reduce((acc: number, d: any) => acc + (d.count || 0), 0);
                const pct = count > 0 ? Math.random() * 40 + 10 : 0; // Demo
                const colors: Record<string, string> = { HOT: 'var(--hot-c)', WARM: 'var(--warm-c)', COLD: 'var(--cold-c)' };
                const bgs: Record<string, string> = { HOT: 'var(--hot-bg)', WARM: 'var(--warm-bg)', COLD: 'var(--cold-bg)' };
                return (
                  <div key={cat} style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className={`badge badge-${cat.toLowerCase()}`}>{cat}</span>
                      </div>
                      <span style={{ fontSize: 13, fontWeight: 600, color: colors[cat] }}>{Math.round(pct)}%</span>
                    </div>
                    <div className="progress-wrap">
                      <div className="progress-bar" style={{ width: `${pct}%`, background: colors[cat] }} />
                    </div>
                  </div>
                );
              })}

              {/* Quick actions */}
              <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <Link to="/contacts" className="btn btn-brand-ghost btn-sm" style={{ justifyContent: 'space-between', width: '100%' }}>
                  <span>Enrichir les contacts manquants</span>
                  <ChevronRight size={13} />
                </Link>
                <Link to="/agent" className="btn btn-secondary btn-sm" style={{ justifyContent: 'space-between', width: '100%' }}>
                  <span>Lancer l'AI Agent</span>
                  <Bot size={13} />
                </Link>
              </div>
            </div>
          </div>

          {/* Signals panel */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-header">
              <div>
                <div className="card-title">Signals récents</div>
                <div className="card-sub">{signalsSummary?.unread || 0} non lus</div>
              </div>
              <Link to="/signals" className="btn btn-ghost btn-xs">Voir tout</Link>
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <SignalsFeed />
            </div>
          </div>
        </div>

        {/* Bottom row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <QuickActions />
          <AIStatus />
        </div>

        <p style={{ fontSize: 11, color: 'var(--tx-muted)', textAlign: 'right' }}>
          Mis à jour : {data ? new Date(data.last_updated).toLocaleString('fr-FR') : '—'}
        </p>
      </div>
    </div>
  );
}

function KpiCard({ label, value, sub, icon, cls, iconCls, trend }: any) {
  return (
    <div className={`kpi-card ${cls}`}>
      <div className={`kpi-icon ${iconCls}`}>{icon}</div>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-sub">
        {trend && <span className="kpi-trend kpi-trend-up">↑ {trend}</span>}
        {' '}{sub}
      </div>
    </div>
  );
}

function SignalsFeed() {
  const { data: signals } = useQuery({
    queryKey: ['signals', { limit: 8 }],
    queryFn: async () => { try { const { data } = await apiClient.get('/signals?limit=8'); return data; } catch { return []; } },
    staleTime: 30_000,
  });

  const colors: Record<string, string> = {
    critical: 'var(--c-red)', warning: 'var(--c-orange)', info: 'var(--c-blue)',
  };

  if (!signals?.length) {
    return (
      <div className="empty-state" style={{ padding: 24 }}>
        <Activity size={28} className="empty-icon" />
        <p style={{ fontSize: 12, color: 'var(--tx-muted)' }}>Aucun signal détecté</p>
      </div>
    );
  }

  return (
    <div style={{ overflowY: 'auto', maxHeight: 240 }}>
      {signals.map((s: any) => (
        <div key={s.id} className="signal-item">
          <div className="signal-dot" style={{ background: colors[s.severity] || 'var(--c-blue)', marginTop: 5 }} />
          <div className="signal-body">
            <div className="signal-title">{s.title}</div>
            <div className="signal-meta">{s.prospect_name}</div>
          </div>
          <div className="signal-time">{new Date(s.created_at).toLocaleDateString('fr-FR')}</div>
        </div>
      ))}
    </div>
  );
}

function QuickActions() {
  const actions = [
    { label: 'Ajouter par SIRET',      icon: '🔍', to: '/prospects',  sub: 'Enrichissement auto' },
    { label: 'Importer CSV',            icon: '📤', to: '/prospects',  sub: 'Batch import' },
    { label: 'Créer une séquence',      icon: '✉️',  to: '/sequences', sub: 'Email automation' },
    { label: 'Détecter les signaux',    icon: '📡', to: '/signals',    sub: 'Sur tous les prospects' },
    { label: 'ABM / TAM sourcing',      icon: '🎯', to: '/abm',        sub: 'Par NAF + région' },
    { label: 'Contact Intelligence',    icon: '🧠', to: '/contacts',   sub: 'Email + téléphone' },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Actions rapides</div>
        <span className="badge badge-purple">⌘K</span>
      </div>
      <div style={{ padding: '8px' }}>
        {actions.map(a => (
          <Link key={a.label} to={a.to}
            style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '9px 10px', borderRadius: 8, textDecoration: 'none', transition: 'background 0.1s' }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-subtle)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            <span style={{ fontSize: 18, width: 32, textAlign: 'center' }}>{a.icon}</span>
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--tx-primary)' }}>{a.label}</div>
              <div style={{ fontSize: 11, color: 'var(--tx-muted)' }}>{a.sub}</div>
            </div>
            <ChevronRight size={14} style={{ marginLeft: 'auto', color: 'var(--tx-muted)' }} />
          </Link>
        ))}
      </div>
    </div>
  );
}

function AIStatus() {
  const { data } = useQuery({
    queryKey: ['ai-providers'],
    queryFn: async () => { try { const { data } = await apiClient.get('/ai/providers'); return data; } catch { return null; } },
    staleTime: 60_000,
  });

  const providers = data?.providers || [];
  const active = providers.filter((p: any) => p.active);

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Intelligence AI</div>
        <span className={`badge ${active.length > 0 ? 'badge-green' : 'badge-gray'}`}>
          {active.length} provider{active.length > 1 ? 's' : ''} actif{active.length > 1 ? 's' : ''}
        </span>
      </div>
      <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {providers.slice(0, 4).map((p: any) => (
          <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
              background: p.active ? 'var(--c-green)' : 'var(--border-strong)',
            }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: p.active ? 'var(--tx-primary)' : 'var(--tx-muted)' }}>
                {p.name}
              </div>
              <div style={{ fontSize: 11, color: 'var(--tx-muted)' }}>
                {p.active ? p.price : `→ Configurer ${p.env_key}`}
              </div>
            </div>
            {p.free && <span className="badge badge-green" style={{ fontSize: 10 }}>gratuit</span>}
            {!p.active && p.signup_url && (
              <a href={p.signup_url} target="_blank" rel="noreferrer"
                className="btn btn-secondary btn-xs" style={{ fontSize: 10 }}>
                Activer
              </a>
            )}
          </div>
        ))}
        <Link to="/settings" className="btn btn-ghost btn-sm" style={{ marginTop: 4, justifyContent: 'center' }}>
          Gérer les providers AI
        </Link>
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 100, borderRadius: 12 }} />)}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 340px', gap: 16 }}>
        {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 280, borderRadius: 12 }} />)}
      </div>
    </div>
  );
}
