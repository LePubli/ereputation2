import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

/* ─────────────────────────────────────────────────────── Types */
interface ICPCriteria {
  naf_codes: string[];
  regions: string[];
  employee_min: number;
  employee_max: number;
  revenue_min: string;
  exclude_no_email: boolean;
  exclude_no_website: boolean;
  score_min: number;
}

interface ABMAccount {
  id: string;
  company_name: string;
  city?: string;
  region?: string;
  naf_label?: string;
  naf_code?: string;
  employee_count?: number;
  score?: number;
  email?: string;
  phone?: string;
  website?: string;
  pipeline_stage?: string;
  abm_tier: 1 | 2 | 3;
  tam_included: boolean;
}

interface TAMStats {
  total_addressable: number;
  serviceable: number;
  obtainable: number;
  already_in_pipeline: number;
  untouched: number;
}

/* ─────────────────────────────────────────────────────── Constants */
const NAF_OPTIONS = [
  { code: '47', label: 'Commerce de détail' },
  { code: '62', label: 'Informatique et logiciels' },
  { code: '56', label: 'Restauration' },
  { code: '41', label: 'Construction' },
  { code: '69', label: 'Droit et comptabilité' },
  { code: '70', label: 'Conseil aux entreprises' },
  { code: '73', label: 'Publicité / études de marché' },
  { code: '74', label: 'Activités créatives' },
  { code: '85', label: 'Enseignement' },
  { code: '86', label: 'Santé' },
  { code: '96', label: 'Autres services personnels' },
  { code: '43', label: 'Travaux de construction spécialisés' },
  { code: '55', label: 'Hébergement' },
  { code: '45', label: 'Commerce/réparation auto' },
  { code: '46', label: 'Commerce de gros' },
];

const REGIONS = [
  'Hauts-de-France', 'Île-de-France', 'Auvergne-Rhône-Alpes',
  'Bretagne', 'Occitanie', 'Normandie', 'Grand Est',
  'Nouvelle-Aquitaine', 'Pays de la Loire', "Provence-Alpes-Côte d'Azur",
  'Bourgogne-Franche-Comté', 'Centre-Val de Loire', 'Corse',
];

const TIER_CONFIG = {
  1: { label: 'Tier 1 — Cible prioritaire', color: '#3fb950', bg: 'rgba(63,185,80,0.1)', icon: '🎯' },
  2: { label: 'Tier 2 — Cible secondaire', color: '#2f81f7', bg: 'rgba(47,129,247,0.1)', icon: '📋' },
  3: { label: 'Tier 3 — Volume', color: '#8b949e', bg: 'rgba(139,148,158,0.1)', icon: '📊' },
};

const DEFAULT_ICP: ICPCriteria = {
  naf_codes: [],
  regions: ['Hauts-de-France'],
  employee_min: 1,
  employee_max: 500,
  revenue_min: '',
  exclude_no_email: false,
  exclude_no_website: false,
  score_min: 0,
};

/* ─────────────────────────────────────────────────────── Component */
export default function ABMPage() {
  const [icp, setIcp] = useState<ICPCriteria>(DEFAULT_ICP);
  const [accounts, setAccounts] = useState<ABMAccount[]>([]);
  const [tamStats, setTamStats] = useState<TAMStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [sourcing, setSourcing] = useState(false);
  const [activeTab, setActiveTab] = useState<'icp' | 'accounts' | 'tam'>('icp');
  const [tierFilter, setTierFilter] = useState<'all' | 1 | 2 | 3>('all');
  const [sourcingProgress, setSourcingProgress] = useState(0);
  const [sourcingStatus, setSourcingStatus] = useState('');

  useEffect(() => { loadABMAccounts(); }, []);

  const loadABMAccounts = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/abm/accounts?limit=200');
      setAccounts(data.items || []);
      setTamStats(data.tam_stats || null);
    } catch { setAccounts([]); } finally { setLoading(false); }
  };

  const runTAMSourcing = async () => {
    setSourcing(true);
    setSourcingProgress(0);
    setSourcingStatus('Connexion à la base INSEE SIRENE...');

    try {
      // Simulated progress — real endpoint is async
      const steps = [
        [10, 'Analyse des codes NAF cibles...'],
        [25, 'Filtrage par région et effectifs...'],
        [45, 'Récupération via INSEE SIRENE...'],
        [65, 'Calcul des scores ICP...'],
        [80, 'Attribution des Tiers ABM...'],
        [90, 'Import dans la base de données...'],
        [100, 'Sourcing terminé !'],
      ];

      for (const [pct, msg] of steps) {
        setSourcingProgress(pct as number);
        setSourcingStatus(msg as string);
        await new Promise(r => setTimeout(r, 600));
      }

      await apiClient.post('/abm/source-tam', { icp });
      await loadABMAccounts();
      setActiveTab('accounts');
    } catch (e) {
      setSourcingStatus('Erreur lors du sourcing');
    } finally {
      setSourcing(false);
      setSourcingProgress(0);
    }
  };

  const assignTier = async (id: string, tier: 1 | 2 | 3) => {
    await apiClient.patch(`/abm/accounts/${id}`, { abm_tier: tier });
    setAccounts(prev => prev.map(a => a.id === id ? { ...a, abm_tier: tier } : a));
  };

  const addToSequence = async (ids: string[]) => {
    await apiClient.post('/abm/enroll-sequence', { account_ids: ids });
  };

  const toggleNaf = (code: string) =>
    setIcp(prev => ({
      ...prev,
      naf_codes: prev.naf_codes.includes(code)
        ? prev.naf_codes.filter(c => c !== code)
        : [...prev.naf_codes, code],
    }));

  const toggleRegion = (region: string) =>
    setIcp(prev => ({
      ...prev,
      regions: prev.regions.includes(region)
        ? prev.regions.filter(r => r !== region)
        : [...prev.regions, region],
    }));

  const filtered = accounts.filter(a =>
    tierFilter === 'all' || a.abm_tier === tierFilter
  );

  const tier1Count = accounts.filter(a => a.abm_tier === 1).length;
  const tier2Count = accounts.filter(a => a.abm_tier === 2).length;
  const tier3Count = accounts.filter(a => a.abm_tier === 3).length;

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', boxSizing: 'border-box', overflow: 'hidden' }}>

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            ABM — Account-Based Marketing
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            Définissez votre ICP, calculez votre TAM, sourcez vos cibles prioritaires
          </p>
        </div>
        {activeTab === 'icp' && (
          <button
            onClick={runTAMSourcing}
            disabled={sourcing}
            style={{
              padding: '0.5rem 1.25rem', borderRadius: '8px',
              background: sourcing ? 'var(--bg-tertiary)' : 'var(--accent-blue)',
              border: 'none', color: '#fff', cursor: sourcing ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem', fontWeight: 600,
              display: 'flex', alignItems: 'center', gap: '0.5rem',
            }}
          >
            {sourcing ? (
              <><Spinner /> {sourcingStatus}</>
            ) : '⚡ Sourcer le TAM via INSEE'}
          </button>
        )}
      </div>

      {/* ── Sourcing progress bar ── */}
      {sourcing && (
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: '10px', padding: '1rem 1.25rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{sourcingStatus}</span>
            <span style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>{sourcingProgress}%</span>
          </div>
          <div style={{ height: '8px', background: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: '4px',
              background: 'linear-gradient(90deg, var(--accent-blue), #8b5cf6)',
              width: `${sourcingProgress}%`, transition: 'width 0.4s ease',
            }} />
          </div>
        </div>
      )}

      {/* ── Tier KPIs ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.875rem' }}>
        {([1, 2, 3] as const).map(tier => {
          const cfg = TIER_CONFIG[tier];
          const count = [tier1Count, tier2Count, tier3Count][tier - 1];
          return (
            <div
              key={tier}
              onClick={() => setTierFilter(tierFilter === tier ? 'all' : tier)}
              style={{
                background: tierFilter === tier ? cfg.bg : 'var(--bg-card)',
                border: `1px solid ${tierFilter === tier ? cfg.color : 'var(--border-color)'}`,
                borderRadius: '10px', padding: '1rem 1.25rem',
                cursor: 'pointer', transition: 'all 0.15s',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 700, color: cfg.color }}>{count}</span>
                <span style={{ fontSize: '1.25rem' }}>{cfg.icon}</span>
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '0.25rem' }}>{cfg.label}</div>
            </div>
          );
        })}
      </div>

      {/* ── Tabs ── */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)' }}>
        {[
          { id: 'icp' as const, label: '🎯 Profil ICP' },
          { id: 'tam' as const, label: '📊 Analyse TAM' },
          { id: 'accounts' as const, label: `🏢 Comptes ABM (${accounts.length})` },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
            padding: '0.75rem 1.25rem', border: 'none',
            borderBottom: `2px solid ${activeTab === tab.id ? 'var(--accent-blue)' : 'transparent'}`,
            background: 'none',
            color: activeTab === tab.id ? 'var(--accent-blue)' : 'var(--text-secondary)',
            cursor: 'pointer', fontSize: '0.875rem',
            fontWeight: activeTab === tab.id ? 600 : 400,
          }}>{tab.label}</button>
        ))}
      </div>

      {/* ──────────────────── ICP TAB ──────────────────── */}
      {activeTab === 'icp' && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', maxWidth: '900px' }}>

            {/* NAF codes */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem', gridColumn: 'span 2' }}>
              <SectionTitle>🏭 Secteurs d'activité ciblés (NAF)</SectionTitle>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
                {NAF_OPTIONS.map(n => (
                  <button key={n.code} onClick={() => toggleNaf(n.code)} style={{
                    padding: '0.375rem 0.875rem', borderRadius: '20px', cursor: 'pointer',
                    background: icp.naf_codes.includes(n.code) ? 'rgba(47,129,247,0.15)' : 'var(--bg-secondary)',
                    border: `1px solid ${icp.naf_codes.includes(n.code) ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
                    color: icp.naf_codes.includes(n.code) ? 'var(--accent-blue)' : 'var(--text-secondary)',
                    fontSize: '0.8125rem', transition: 'all 0.1s',
                  }}>
                    {icp.naf_codes.includes(n.code) ? '✓ ' : ''}{n.code} — {n.label}
                  </button>
                ))}
              </div>
              {icp.naf_codes.length === 0 && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', marginTop: '0.75rem' }}>
                  Aucun secteur sélectionné = tous les secteurs
                </p>
              )}
            </div>

            {/* Régions */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem' }}>
              <SectionTitle>📍 Régions cibles</SectionTitle>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', marginTop: '0.75rem' }}>
                {REGIONS.map(r => (
                  <label key={r} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={icp.regions.includes(r)}
                      onChange={() => toggleRegion(r)}
                      style={{ cursor: 'pointer', accentColor: 'var(--accent-blue)' }}
                    />
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>{r}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Effectifs + filtres */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem' }}>
                <SectionTitle>👥 Effectif cible</SectionTitle>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginTop: '0.75rem' }}>
                  <NumField label="Min" value={icp.employee_min} onChange={v => setIcp(p => ({ ...p, employee_min: v }))} />
                  <NumField label="Max" value={icp.employee_max} onChange={v => setIcp(p => ({ ...p, employee_max: v }))} />
                </div>
                {/* Visual slider range */}
                <div style={{ marginTop: '0.75rem', padding: '0.5rem 0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.7rem', marginBottom: '0.25rem' }}>
                    <span>1</span><span>50</span><span>200</span><span>500+</span>
                  </div>
                  <div style={{ height: '6px', background: 'var(--bg-tertiary)', borderRadius: '3px', position: 'relative' }}>
                    <div style={{
                      position: 'absolute',
                      left: `${Math.min((icp.employee_min / 500) * 100, 100)}%`,
                      right: `${100 - Math.min((icp.employee_max / 500) * 100, 100)}%`,
                      height: '100%', background: 'var(--accent-blue)', borderRadius: '3px',
                    }} />
                  </div>
                </div>
              </div>

              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem' }}>
                <SectionTitle>🔽 Filtres qualité</SectionTitle>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.75rem' }}>
                  <ToggleRow label="Exclure sans email" value={icp.exclude_no_email}
                    onChange={v => setIcp(p => ({ ...p, exclude_no_email: v }))} />
                  <ToggleRow label="Exclure sans site web" value={icp.exclude_no_website}
                    onChange={v => setIcp(p => ({ ...p, exclude_no_website: v }))} />
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>
                      Score minimum ({icp.score_min}/100)
                    </label>
                    <input type="range" min={0} max={100} value={icp.score_min}
                      onChange={e => setIcp(p => ({ ...p, score_min: parseInt(e.target.value) }))}
                      style={{ width: '100%', accentColor: 'var(--accent-blue)' }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* ICP Summary */}
            <div style={{
              background: 'rgba(47,129,247,0.06)', border: '1px solid rgba(47,129,247,0.2)',
              borderRadius: '10px', padding: '1.25rem', gridColumn: 'span 2',
            }}>
              <SectionTitle>📋 Résumé ICP actuel</SectionTitle>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
                <ICPBadge icon="🏭" label={icp.naf_codes.length ? `${icp.naf_codes.length} secteur(s)` : 'Tous secteurs'} />
                <ICPBadge icon="📍" label={icp.regions.length ? icp.regions.join(', ').slice(0, 50) : 'Toutes régions'} />
                <ICPBadge icon="👥" label={`${icp.employee_min}–${icp.employee_max} employés`} />
                {icp.exclude_no_email && <ICPBadge icon="📧" label="Avec email uniquement" color="var(--accent-green)" />}
                {icp.exclude_no_website && <ICPBadge icon="🌐" label="Avec site web uniquement" color="var(--accent-green)" />}
                {icp.score_min > 0 && <ICPBadge icon="⭐" label={`Score ≥ ${icp.score_min}`} color="var(--accent-orange)" />}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ──────────────────── TAM TAB ──────────────────── */}
      {activeTab === 'tam' && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          {!tamStats ? (
            <div style={{
              textAlign: 'center', padding: '4rem',
              border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)',
            }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
              <p style={{ fontWeight: 600, color: 'var(--text-secondary)', fontSize: '1rem' }}>
                Aucune analyse TAM disponible
              </p>
              <p>Configurez votre ICP et lancez le sourcing pour calculer votre marché total adressable</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', maxWidth: '800px' }}>
              {/* TAM Funnel */}
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.5rem', gridColumn: 'span 2' }}>
                <SectionTitle>📐 Entonnoir TAM → SAM → SOM</SectionTitle>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1.25rem' }}>
                  {[
                    { label: 'TAM — Total Addressable Market', value: tamStats.total_addressable, color: '#2f81f7', width: 100, desc: 'Toutes entreprises correspondant aux critères ICP' },
                    { label: 'SAM — Serviceable Addressable', value: tamStats.serviceable, color: '#8b5cf6', width: Math.round(tamStats.serviceable / tamStats.total_addressable * 100), desc: 'Entreprises atteignables (avec email ou téléphone)' },
                    { label: 'SOM — Serviceable Obtainable', value: tamStats.obtainable, color: '#3fb950', width: Math.round(tamStats.obtainable / tamStats.total_addressable * 100), desc: 'Cible réaliste en 12 mois (score ≥ 50)' },
                  ].map(item => (
                    <div key={item.label} style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                      <div style={{ width: '200px', flexShrink: 0 }}>
                        <div style={{ fontWeight: 600, color: item.color, fontSize: '0.875rem' }}>{item.label.split('—')[0].trim()}</div>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{item.label.split('—')[1]?.trim()}</div>
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{item.desc}</span>
                          <span style={{ fontWeight: 700, color: item.color, fontSize: '1rem' }}>
                            {item.value.toLocaleString('fr-FR')}
                          </span>
                        </div>
                        <div style={{ height: '8px', background: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', background: item.color, borderRadius: '4px', width: `${item.width}%`, transition: 'width 0.6s ease' }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Pipeline coverage */}
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem' }}>
                <SectionTitle>🎯 Couverture Pipeline</SectionTitle>
                <div style={{ marginTop: '1rem' }}>
                  <div style={{ position: 'relative', width: '120px', height: '120px', margin: '0 auto' }}>
                    <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                      <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--bg-tertiary)" strokeWidth="3" />
                      <circle cx="18" cy="18" r="15.9" fill="none" stroke="#2f81f7" strokeWidth="3"
                        strokeDasharray={`${tamStats.already_in_pipeline / tamStats.total_addressable * 100} 100`}
                        strokeLinecap="round" />
                    </svg>
                    <div style={{
                      position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
                      alignItems: 'center', justifyContent: 'center',
                    }}>
                      <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-blue)' }}>
                        {Math.round(tamStats.already_in_pipeline / tamStats.total_addressable * 100)}%
                      </span>
                      <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>couvert</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '1rem' }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#2f81f7' }}>{tamStats.already_in_pipeline.toLocaleString()}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>En pipeline</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#3fb950' }}>{tamStats.untouched.toLocaleString()}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Non contactés</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem' }}>
                <SectionTitle>💡 Recommandations</SectionTitle>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.875rem' }}>
                  {[
                    { icon: '🎯', text: `Concentrez vos efforts Tier 1 sur ${Math.min(tier1Count, 50)} comptes prioritaires`, color: '#3fb950' },
                    { icon: '📧', text: `${tamStats.untouched.toLocaleString()} entreprises n'ont jamais été contactées`, color: '#2f81f7' },
                    { icon: '⚡', text: 'Enrichissez les Tier 1 pour maximiser les taux de contact', color: '#d29922' },
                  ].map((r, i) => (
                    <div key={i} style={{ display: 'flex', gap: '0.625rem', alignItems: 'flex-start' }}>
                      <span style={{ fontSize: '1rem', flexShrink: 0 }}>{r.icon}</span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', lineHeight: 1.4 }}>{r.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ──────────────────── ACCOUNTS TAB ──────────────────── */}
      {activeTab === 'accounts' && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          {loading ? (
            <div style={{ display: 'grid', gap: '0.625rem' }}>
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} style={{ height: '64px', background: 'var(--bg-card)', borderRadius: '8px', animation: 'pulse 1.5s ease infinite' }} />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState icon="🏢" title="Aucun compte ABM" desc="Définissez votre ICP et sourcez vos comptes via INSEE" />
          ) : (
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              {filtered.map(account => {
                const tierCfg = TIER_CONFIG[account.abm_tier || 3];
                return (
                  <div key={account.id} style={{
                    background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                    borderLeft: `4px solid ${tierCfg.color}`,
                    borderRadius: '8px', padding: '0.875rem',
                    display: 'flex', alignItems: 'center', gap: '1rem',
                  }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
                          {account.company_name}
                        </span>
                        <span style={{
                          padding: '1px 7px', borderRadius: '20px', fontSize: '0.7rem',
                          background: tierCfg.bg, color: tierCfg.color,
                        }}>
                          {tierCfg.icon} T{account.abm_tier}
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: '0.75rem', color: 'var(--text-muted)', fontSize: '0.75rem', flexWrap: 'wrap' }}>
                        {account.city && <span>📍 {account.city}</span>}
                        {account.naf_label && <span>🏭 {account.naf_label.slice(0, 30)}</span>}
                        {account.employee_count && <span>👥 {account.employee_count}</span>}
                        {account.email && <span style={{ color: 'var(--accent-green)' }}>📧</span>}
                        {account.phone && <span style={{ color: 'var(--accent-green)' }}>📞</span>}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                      {/* Score */}
                      {account.score !== undefined && (
                        <div style={{
                          width: '36px', height: '36px', borderRadius: '50%',
                          border: `2px solid ${account.score >= 75 ? '#3fb950' : account.score >= 50 ? '#2f81f7' : '#d29922'}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '0.6875rem', fontWeight: 700,
                          color: account.score >= 75 ? '#3fb950' : account.score >= 50 ? '#2f81f7' : '#d29922',
                        }}>{account.score}</div>
                      )}

                      {/* Tier selector */}
                      <select
                        value={account.abm_tier}
                        onChange={e => assignTier(account.id, parseInt(e.target.value) as 1 | 2 | 3)}
                        style={{
                          padding: '0.25rem 0.5rem', borderRadius: '6px',
                          background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                          color: 'var(--text-secondary)', fontSize: '0.75rem', cursor: 'pointer',
                        }}
                      >
                        <option value={1}>🎯 Tier 1</option>
                        <option value={2}>📋 Tier 2</option>
                        <option value={3}>📊 Tier 3</option>
                      </select>

                      {/* Add to sequence */}
                      <button
                        onClick={() => addToSequence([account.id])}
                        title="Inscrire en séquence email"
                        style={{
                          padding: '0.25rem 0.625rem', borderRadius: '6px', fontSize: '0.75rem',
                          background: 'rgba(47,129,247,0.1)', border: '1px solid rgba(47,129,247,0.3)',
                          color: 'var(--accent-blue)', cursor: 'pointer',
                        }}
                      >📧 Séquence</button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}

/* ── Sub-components ── */

function Spinner() {
  return (
    <span style={{
      display: 'inline-block', width: '14px', height: '14px',
      border: '2px solid rgba(255,255,255,0.3)',
      borderTopColor: '#fff', borderRadius: '50%',
      animation: 'spin 0.7s linear infinite',
    }} />
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.8125rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
      {children}
    </div>
  );
}

function ICPBadge({ icon, label, color = 'var(--accent-blue)' }: { icon: string; label: string; color?: string }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '0.375rem',
      padding: '0.25rem 0.75rem', borderRadius: '20px',
      background: `${color}18`, border: `1px solid ${color}44`,
      color, fontSize: '0.8125rem',
    }}>
      {icon} {label}
    </span>
  );
}

function NumField({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{label}</label>
      <input
        type="number" value={value} min={0}
        onChange={e => onChange(parseInt(e.target.value) || 0)}
        style={{
          width: '100%', padding: '0.5rem 0.625rem',
          background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
          borderRadius: '6px', color: 'var(--text-primary)', fontSize: '0.875rem',
          outline: 'none', boxSizing: 'border-box',
        }}
      />
    </div>
  );
}

function ToggleRow({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{label}</span>
      <button onClick={() => onChange(!value)} style={{
        width: '40px', height: '22px', borderRadius: '11px', border: 'none',
        background: value ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
        cursor: 'pointer', position: 'relative', transition: 'background 0.2s',
      }}>
        <div style={{
          position: 'absolute', top: '3px', left: value ? '20px' : '3px',
          width: '16px', height: '16px', borderRadius: '50%', background: '#fff',
          transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
        }} />
      </button>
    </div>
  );
}

function EmptyState({ icon, title, desc }: { icon: string; title: string; desc: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '4rem', border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)' }}>
      <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>{icon}</div>
      <p style={{ fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.9375rem' }}>{title}</p>
      <p style={{ fontSize: '0.875rem', marginTop: '0.375rem' }}>{desc}</p>
    </div>
  );
}
