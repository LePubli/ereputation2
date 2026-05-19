import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { Power, Settings, Package, Search, CheckCircle2, XCircle, Lock, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

interface Plugin {
  name: string;
  display_name: string;
  version: string;
  description: string;
  author: string;
  category: string;
  icon: string;
  is_active: boolean;
  is_core: boolean;
  is_loaded: boolean;
  config: Record<string, unknown>;
  dependencies: string[];
}

const CATEGORY_LABELS: Record<string, string> = {
  core: '🔒 Core',
  crm: '📊 CRM',
  sourcing: '🔍 Sourcing',
  marketing: '📧 Marketing',
  intelligence: '🤖 Intelligence',
  tools: '🔧 Outils',
};

const CATEGORY_COLORS: Record<string, string> = {
  core: '#dc3545', crm: '#0d6efd', sourcing: '#198754',
  marketing: '#fd7e14', intelligence: '#6f42c1', tools: '#6c757d',
};

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState('all');
  const [filterState, setFilterState] = useState<'all' | 'active' | 'inactive'>('all');
  const [toggling, setToggling] = useState<string | null>(null);
  const [selected, setSelected] = useState<Plugin | null>(null);

  useEffect(() => { load(); }, []);

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/system/plugins');
      setPlugins(data.items || []);
    } catch { toast.error('Erreur chargement plugins'); }
    finally { setLoading(false); }
  };

  const toggle = async (plugin: Plugin) => {
    if (plugin.is_core) return;
    setToggling(plugin.name);
    try {
      const result = await apiClient.post(`/system/plugins/${plugin.name}/toggle`, {});
      setPlugins(prev => prev.map(p =>
        p.name === plugin.name ? { ...p, is_active: result.is_active } : p
      ));
      toast.success(result.message);
      if (selected?.name === plugin.name) {
        setSelected(prev => prev ? { ...prev, is_active: result.is_active } : null);
      }
    } catch (e: any) {
      toast.error(e?.message || 'Erreur toggle plugin');
    } finally { setToggling(null); }
  };

  const filtered = plugins.filter(p => {
    const matchSearch = !search || p.display_name.toLowerCase().includes(search.toLowerCase()) ||
      p.description.toLowerCase().includes(search.toLowerCase());
    const matchCat = filterCat === 'all' || p.category === filterCat;
    const matchState = filterState === 'all' || (filterState === 'active' ? p.is_active : !p.is_active);
    return matchSearch && matchCat && matchState;
  });

  const categories = ['all', ...new Set(plugins.map(p => p.category))];
  const stats = {
    total: plugins.length,
    active: plugins.filter(p => p.is_active).length,
    inactive: plugins.filter(p => !p.is_active).length,
  };

  return (
    <div style={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <div style={{ padding: '1.25rem 1.5rem', background: '#fff', borderBottom: '1px solid var(--border-color)', flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              Plugins
            </h1>
            <p style={{ margin: '3px 0 0', fontSize: '.8125rem', color: 'var(--text-muted)' }}>
              {stats.active} actifs · {stats.inactive} inactifs · {stats.total} total
            </p>
          </div>
          <button onClick={load} style={{ display: 'flex', alignItems: 'center', gap: '.375rem', padding: '.4375rem .875rem', borderRadius: 8, background: '#f0f4ff', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '.8125rem' }}>
            <RefreshCw size={13} /> Actualiser
          </button>
        </div>

        {/* Filtres */}
        <div style={{ display: 'flex', gap: '.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem', background: '#f0f4ff', border: '1px solid var(--border-color)', borderRadius: 8, padding: '.375rem .75rem', flex: 1, maxWidth: 280 }}>
            <Search size={13} color="var(--text-muted)" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Rechercher un plugin..."
              style={{ background: 'none', border: 'none', outline: 'none', fontSize: '.8125rem', color: 'var(--text-primary)', flex: 1 }} />
          </div>

          {/* State filter */}
          <div style={{ display: 'flex', background: '#f0f4ff', border: '1px solid var(--border-color)', borderRadius: 8, padding: 3, gap: 2 }}>
            {(['all', 'active', 'inactive'] as const).map(s => (
              <button key={s} onClick={() => setFilterState(s)}
                style={{ padding: '.3125rem .75rem', borderRadius: 6, border: 'none', fontSize: '.8125rem', cursor: 'pointer', background: filterState === s ? '#fff' : 'transparent', color: filterState === s ? 'var(--accent-blue)' : 'var(--text-secondary)', fontWeight: filterState === s ? 600 : 400, transition: 'all .15s', boxShadow: filterState === s ? '0 1px 3px rgba(0,0,0,.1)' : 'none' }}>
                {s === 'all' ? 'Tous' : s === 'active' ? '✓ Actifs' : '○ Inactifs'}
              </button>
            ))}
          </div>

          {/* Category filter */}
          <select value={filterCat} onChange={e => setFilterCat(e.target.value)}
            style={{ padding: '.375rem .75rem', borderRadius: 8, border: '1px solid var(--border-color)', background: '#fff', color: 'var(--text-secondary)', fontSize: '.8125rem', outline: 'none' }}>
            {categories.map(c => (
              <option key={c} value={c}>{c === 'all' ? 'Toutes catégories' : CATEGORY_LABELS[c] || c}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto', display: 'flex' }}>

        {/* Plugin grid */}
        <div style={{ flex: 1, padding: '1.25rem', overflow: 'auto' }}>
          {loading ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} style={{ height: 130, borderRadius: 10, background: 'linear-gradient(90deg,#eef2ff 25%,#e5eaf8 50%,#eef2ff 75%)', backgroundSize: '200%', animation: 'shimmer 1.5s infinite' }} />
              ))}
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
              {filtered.map(plugin => (
                <PluginCard
                  key={plugin.name}
                  plugin={plugin}
                  onToggle={toggle}
                  onSelect={setSelected}
                  isSelected={selected?.name === plugin.name}
                  isToggling={toggling === plugin.name}
                />
              ))}
              {filtered.length === 0 && (
                <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  <Package size={40} style={{ opacity: .3, marginBottom: '.75rem' }} />
                  <p>Aucun plugin trouvé</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <div style={{ width: 320, borderLeft: '1px solid var(--border-color)', background: '#fff', overflow: 'auto', flexShrink: 0 }}>
            <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontSize: '1.5rem', marginBottom: '.375rem' }}>{selected.icon}</div>
                  <div style={{ fontWeight: 700, fontSize: '.9375rem', color: 'var(--text-primary)' }}>{selected.display_name}</div>
                  <div style={{ fontSize: '.75rem', color: 'var(--text-muted)' }}>v{selected.version} · {selected.author}</div>
                </div>
                <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.25rem', padding: '0' }}>×</button>
              </div>
            </div>

            <div style={{ padding: '1rem' }}>
              <p style={{ fontSize: '.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1rem' }}>
                {selected.description}
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem', marginBottom: '1.25rem' }}>
                <InfoRow label="Catégorie" value={CATEGORY_LABELS[selected.category] || selected.category} />
                <InfoRow label="Statut" value={selected.is_active ? '● Actif' : '○ Inactif'} color={selected.is_active ? '#198754' : '#6c757d'} />
                <InfoRow label="Core" value={selected.is_core ? 'Oui' : 'Non'} />
                {selected.dependencies.length > 0 && (
                  <InfoRow label="Dépendances" value={selected.dependencies.join(', ')} />
                )}
              </div>

              {!selected.is_core && (
                <button
                  onClick={() => toggle(selected)}
                  disabled={toggling === selected.name}
                  style={{
                    width: '100%', padding: '.625rem', borderRadius: 8, border: 'none', cursor: 'pointer',
                    fontWeight: 600, fontSize: '.875rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '.5rem',
                    background: selected.is_active ? 'rgba(220,53,69,.1)' : 'rgba(25,135,84,.1)',
                    color: selected.is_active ? '#dc3545' : '#198754',
                    transition: 'all .15s',
                  }}
                >
                  <Power size={15} />
                  {selected.is_active ? 'Désactiver le plugin' : 'Activer le plugin'}
                </button>
              )}

              {selected.is_core && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem', padding: '.625rem .875rem', borderRadius: 8, background: 'rgba(220,53,69,.06)', border: '1px solid rgba(220,53,69,.2)', color: '#dc3545', fontSize: '.8125rem' }}>
                  <Lock size={13} /> Plugin core — ne peut pas être désactivé
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <style>{`@keyframes shimmer { 0%{background-position:-200% center} 100%{background-position:200% center} }`}</style>
    </div>
  );
}

function PluginCard({ plugin, onToggle, onSelect, isSelected, isToggling }: {
  plugin: Plugin;
  onToggle: (p: Plugin) => void;
  onSelect: (p: Plugin) => void;
  isSelected: boolean;
  isToggling: boolean;
}) {
  const catColor = CATEGORY_COLORS[plugin.category] || '#6c757d';

  return (
    <div
      onClick={() => onSelect(plugin)}
      style={{
        background: '#fff',
        border: `1px solid ${isSelected ? 'var(--accent-blue)' : 'var(--border-color)'}`,
        borderRadius: 10, padding: '1rem',
        cursor: 'pointer', transition: 'all .15s',
        boxShadow: isSelected ? '0 0 0 3px rgba(13,110,253,.1)' : 'var(--shadow-card)',
        opacity: !plugin.is_active && !plugin.is_core ? .75 : 1,
      }}
      onMouseEnter={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.borderColor = '#c8d0e4'; }}
      onMouseLeave={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)'; }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '.625rem' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: `${catColor}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem', flexShrink: 0 }}>
            {plugin.icon}
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '.875rem', color: 'var(--text-primary)' }}>{plugin.display_name}</div>
            <div style={{ fontSize: '.7rem', color: 'var(--text-muted)' }}>v{plugin.version} · {plugin.author}</div>
          </div>
        </div>

        {/* Toggle switch */}
        {!plugin.is_core ? (
          <button
            onClick={e => { e.stopPropagation(); onToggle(plugin); }}
            disabled={isToggling}
            style={{
              position: 'relative', width: 40, height: 22, borderRadius: 11,
              background: plugin.is_active ? 'var(--accent-blue)' : '#dee2e6',
              border: 'none', cursor: 'pointer', transition: 'background .2s',
              flexShrink: 0,
            }}
          >
            <span style={{
              position: 'absolute', top: 3, left: plugin.is_active ? 21 : 3,
              width: 16, height: 16, borderRadius: '50%', background: '#fff',
              transition: 'left .2s', boxShadow: '0 1px 3px rgba(0,0,0,.3)',
              display: 'block',
            }} />
          </button>
        ) : (
          <span style={{ padding: '2px 8px', borderRadius: 20, fontSize: '.7rem', fontWeight: 700, background: 'rgba(220,53,69,.1)', color: '#dc3545' }}>
            <Lock size={10} style={{ verticalAlign: 'middle', marginRight: 3 }} />CORE
          </span>
        )}
      </div>

      <p style={{ margin: '0 0 .75rem', fontSize: '.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
        {plugin.description}
      </p>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ padding: '2px 8px', borderRadius: 20, fontSize: '.7rem', fontWeight: 600, background: `${catColor}12`, color: catColor, border: `1px solid ${catColor}25` }}>
          {CATEGORY_LABELS[plugin.category] || plugin.category}
        </span>
        <span style={{ fontSize: '.75rem', color: plugin.is_active ? '#198754' : '#adb5bd', display: 'flex', alignItems: 'center', gap: 3 }}>
          {plugin.is_active
            ? <><CheckCircle2 size={12} /> Actif</>
            : <><XCircle size={12} /> Inactif</>
          }
        </span>
      </div>
    </div>
  );
}

function InfoRow({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '.3125rem 0', borderBottom: '1px solid #f8f9fc' }}>
      <span style={{ fontSize: '.75rem', color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontSize: '.75rem', fontWeight: 500, color: color || 'var(--text-primary)' }}>{value}</span>
    </div>
  );
}
