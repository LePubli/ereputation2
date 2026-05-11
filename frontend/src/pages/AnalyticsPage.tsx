import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface KpiData {
  total_prospects: number;
  prospects_this_month: number;
  prospects_with_email: number;
  prospects_with_phone: number;
  avg_score: number;
  pipeline_value: Record<string, number>;
  score_distribution: { range: string; count: number }[];
  top_regions: { region: string; count: number }[];
  top_naf: { naf_label: string; count: number }[];
  daily_additions: { date: string; count: number }[];
  source_breakdown: { source: string; count: number }[];
  enrichment_rate: number;
  conversion_rate: number;
}

const STAGE_COLORS: Record<string, string> = {
  'Nouveau': '#8b949e',
  'Contacté': '#2f81f7',
  'Qualifié': '#8b5cf6',
  'Proposition': '#d29922',
  'Négociation': '#f97316',
  'Gagné': '#3fb950',
  'Perdu': '#f85149',
};

export default function AnalyticsPage() {
  const [kpis, setKpis] = useState<KpiData | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d' | 'all'>('30d');

  useEffect(() => { loadKpis(); }, [period]);

  const loadKpis = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get(`/analytics/kpis?period=${period}`);
      setKpis(data);
    } catch {
      // Mock data for demo
      setKpis({
        total_prospects: 1247,
        prospects_this_month: 183,
        prospects_with_email: 421,
        prospects_with_phone: 892,
        avg_score: 58,
        pipeline_value: { Nouveau: 312, Contacté: 245, Qualifié: 198, Proposition: 124, Négociation: 87, Gagné: 156, Perdu: 125 },
        score_distribution: [
          { range: '0-24', count: 187 }, { range: '25-49', count: 321 },
          { range: '50-74', count: 498 }, { range: '75-100', count: 241 },
        ],
        top_regions: [
          { region: 'Hauts-de-France', count: 432 }, { region: 'Île-de-France', count: 287 },
          { region: 'Auvergne-Rhône-Alpes', count: 198 }, { region: 'Bretagne', count: 145 },
          { region: 'Occitanie', count: 112 },
        ],
        top_naf: [
          { naf_label: 'Commerce de détail', count: 198 },
          { naf_label: 'Activités informatiques', count: 167 },
          { naf_label: 'Restauration', count: 145 },
          { naf_label: 'Construction', count: 132 },
          { naf_label: 'Services aux entreprises', count: 118 },
        ],
        daily_additions: Array.from({ length: 30 }, (_, i) => ({
          date: new Date(Date.now() - (29 - i) * 86400000).toISOString().slice(0, 10),
          count: Math.floor(Math.random() * 15) + 2,
        })),
        source_breakdown: [
          { source: 'INSEE', count: 487 }, { source: 'Pages Jaunes', count: 312 },
          { source: 'Google Maps', count: 245 }, { source: 'Société.com', count: 132 },
          { source: 'Pappers', count: 71 },
        ],
        enrichment_rate: 34,
        conversion_rate: 12,
      });
    } finally { setLoading(false); }
  };

  const maxDailyCount = kpis ? Math.max(...(kpis.daily_additions.map(d => d.count) || [1])) : 1;
  const totalPipeline = kpis ? Object.values(kpis.pipeline_value).reduce((a, b) => a + b, 0) : 0;
  const maxRegionCount = kpis ? Math.max(...kpis.top_regions.map(r => r.count)) : 1;
  const maxNafCount = kpis ? Math.max(...kpis.top_naf.map(n => n.count)) : 1;

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', boxSizing: 'border-box', overflow: 'auto' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Analytics & Reporting
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            Vue d'ensemble de votre prospection commerciale
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.375rem' }}>
          {(['7d', '30d', '90d', 'all'] as const).map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              style={{
                padding: '0.375rem 0.875rem', borderRadius: '8px', cursor: 'pointer',
                background: period === p ? 'rgba(47,129,247,0.15)' : 'var(--bg-card)',
                border: `1px solid ${period === p ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
                color: period === p ? 'var(--accent-blue)' : 'var(--text-secondary)',
                fontSize: '0.8125rem', transition: 'all 0.15s',
              }}
            >
              {{ '7d': '7 jours', '30d': '30 jours', '90d': '90 jours', 'all': 'Tout' }[p]}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.875rem' }}>
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} style={{ height: '90px', background: 'var(--bg-card)', borderRadius: '10px', animation: 'pulse 1.5s ease infinite' }} />
          ))}
        </div>
      ) : kpis && (
        <>
          {/* Primary KPIs */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.875rem' }}>
            {[
              { label: 'Total prospects', value: kpis.total_prospects.toLocaleString('fr-FR'), icon: '🏢', color: '#2f81f7', sub: `+${kpis.prospects_this_month} ce mois` },
              { label: 'Score moyen', value: kpis.avg_score + '/100', icon: '⭐', color: '#d29922', sub: 'Qualité globale' },
              { label: 'Avec email', value: kpis.prospects_with_email.toLocaleString('fr-FR'), icon: '📧', color: '#3fb950', sub: `${Math.round(kpis.prospects_with_email / kpis.total_prospects * 100)}% de la base` },
              { label: 'Avec téléphone', value: kpis.prospects_with_phone.toLocaleString('fr-FR'), icon: '📞', color: '#8b5cf6', sub: `${Math.round(kpis.prospects_with_phone / kpis.total_prospects * 100)}% de la base` },
              { label: 'Taux enrichissement', value: kpis.enrichment_rate + '%', icon: '⚡', color: '#f97316', sub: 'Données complétées' },
              { label: 'Taux conversion', value: kpis.conversion_rate + '%', icon: '🎯', color: '#ec4899', sub: 'Lead → Prospect' },
            ].map(kpi => (
              <div key={kpi.label} style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: '10px', padding: '1rem 1.25rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{kpi.label}</span>
                  <span style={{ fontSize: '1.125rem' }}>{kpi.icon}</span>
                </div>
                <div style={{ fontSize: '1.625rem', fontWeight: 700, color: kpi.color, lineHeight: 1 }}>{kpi.value}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: '0.375rem' }}>{kpi.sub}</div>
              </div>
            ))}
          </div>

          {/* Charts row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>

            {/* Pipeline funnel */}
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '10px', padding: '1.25rem',
            }}>
              <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1.25rem' }}>
                📊 Répartition Pipeline
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
                {Object.entries(kpis.pipeline_value).map(([stage, count]) => {
                  const pct = Math.round(count / totalPipeline * 100);
                  return (
                    <div key={stage}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                        <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{stage}</span>
                        <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{count} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({pct}%)</span></span>
                      </div>
                      <div style={{ height: '6px', background: 'var(--bg-tertiary)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%', borderRadius: '3px',
                          background: STAGE_COLORS[stage] || '#8b949e',
                          width: `${pct}%`, transition: 'width 0.6s ease',
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Score distribution */}
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '10px', padding: '1.25rem',
            }}>
              <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1.25rem' }}>
                🎯 Distribution des scores
              </h3>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.75rem', height: '120px', padding: '0 0.25rem' }}>
                {kpis.score_distribution.map((bucket, i) => {
                  const maxBucket = Math.max(...kpis.score_distribution.map(b => b.count));
                  const h = Math.round(bucket.count / maxBucket * 100);
                  const colors = ['#f85149', '#d29922', '#2f81f7', '#3fb950'];
                  return (
                    <div key={bucket.range} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.375rem' }}>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{bucket.count}</span>
                      <div style={{ width: '100%', height: `${h}%`, background: colors[i], borderRadius: '4px 4px 0 0', transition: 'height 0.5s ease', minHeight: '4px' }} />
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{bucket.range}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Daily chart */}
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-color)',
            borderRadius: '10px', padding: '1.25rem',
          }}>
            <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1.25rem' }}>
              📈 Ajouts quotidiens ({period})
            </h3>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '3px', height: '80px' }}>
              {kpis.daily_additions.slice(-30).map((day, i) => {
                const h = Math.max(Math.round(day.count / maxDailyCount * 100), 4);
                return (
                  <div
                    key={day.date}
                    title={`${day.date}: ${day.count} prospects`}
                    style={{
                      flex: 1, height: `${h}%`,
                      background: i === kpis.daily_additions.length - 1 ? 'var(--accent-blue)' : 'rgba(47,129,247,0.4)',
                      borderRadius: '2px 2px 0 0', minWidth: '3px',
                      cursor: 'default', transition: 'background 0.1s',
                    }}
                    onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = 'var(--accent-blue)'}
                    onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = i === kpis.daily_additions.length - 1 ? 'var(--accent-blue)' : 'rgba(47,129,247,0.4)'}
                  />
                );
              })}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.375rem', color: 'var(--text-muted)', fontSize: '0.7rem' }}>
              <span>{kpis.daily_additions[0]?.date.slice(5)}</span>
              <span>{kpis.daily_additions[Math.floor(kpis.daily_additions.length / 2)]?.date.slice(5)}</span>
              <span>{kpis.daily_additions[kpis.daily_additions.length - 1]?.date.slice(5)}</span>
            </div>
          </div>

          {/* Bottom row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>

            {/* Top regions */}
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '10px', padding: '1.25rem',
            }}>
              <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1rem' }}>
                📍 Top régions
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {kpis.top_regions.map((r, i) => (
                  <div key={r.region}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        <span style={{ color: 'var(--text-muted)', marginRight: '0.375rem' }}>{i + 1}.</span>{r.region}
                      </span>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>{r.count}</span>
                    </div>
                    <div style={{ height: '4px', background: 'var(--bg-tertiary)', borderRadius: '2px' }}>
                      <div style={{
                        height: '100%', borderRadius: '2px',
                        background: `hsl(${210 + i * 20}, 70%, 60%)`,
                        width: `${Math.round(r.count / maxRegionCount * 100)}%`,
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top NAF */}
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '10px', padding: '1.25rem',
            }}>
              <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1rem' }}>
                🏭 Top secteurs NAF
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {kpis.top_naf.map((n, i) => (
                  <div key={n.naf_label}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '70%' }}>
                        <span style={{ color: 'var(--text-muted)', marginRight: '0.375rem' }}>{i + 1}.</span>{n.naf_label}
                      </span>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>{n.count}</span>
                    </div>
                    <div style={{ height: '4px', background: 'var(--bg-tertiary)', borderRadius: '2px' }}>
                      <div style={{
                        height: '100%', borderRadius: '2px',
                        background: `hsl(${270 + i * 25}, 70%, 60%)`,
                        width: `${Math.round(n.count / maxNafCount * 100)}%`,
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Source breakdown */}
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '10px', padding: '1.25rem',
            }}>
              <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1rem' }}>
                🔗 Sources de données
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {kpis.source_breakdown.map((s, i) => {
                  const total = kpis.source_breakdown.reduce((a, b) => a + b.count, 0);
                  const pct = Math.round(s.count / total * 100);
                  const colors = ['#2f81f7', '#3fb950', '#d29922', '#8b5cf6', '#f97316'];
                  return (
                    <div key={s.source} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: colors[i], flexShrink: 0 }} />
                      <span style={{ flex: 1, fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{s.source}</span>
                      <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>{pct}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </>
      )}

      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}
