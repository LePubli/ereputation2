import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface Plugin {
  name: string;
  version: string;
  description: string;
  enabled: boolean;
  routes_count?: number;
  status?: 'ok' | 'error' | 'warning';
  error?: string;
  category?: string;
}

const CATEGORY_CONFIG: Record<string, { icon: string; color: string }> = {
  core: { icon: '⚙️', color: 'var(--accent-blue)' },
  intelligence: { icon: '🧠', color: 'var(--accent-purple)' },
  marketing: { icon: '📢', color: 'var(--accent-orange)' },
  sales: { icon: '💼', color: 'var(--accent-green)' },
  integration: { icon: '🔌', color: '#ec4899' },
  system: { icon: '🖥️', color: 'var(--text-muted)' },
};

const STATUS_CONFIG = {
  ok: { icon: '✅', label: 'Opérationnel', color: 'var(--accent-green)' },
  warning: { icon: '⚠️', label: 'Attention', color: 'var(--accent-orange)' },
  error: { icon: '❌', label: 'Erreur', color: 'var(--accent-red)' },
};

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [search, setSearch] = useState('');

  useEffect(() => { loadPlugins(); }, []);

  const loadPlugins = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/system/plugins');
      setPlugins(data.plugins || []);
    } catch { setPlugins([]); } finally { setLoading(false); }
  };

  const toggle = async (name: string, current: boolean) => {
    setToggling(name);
    try {
      await apiClient.post(`/system/plugins/${name}/${current ? 'disable' : 'enable'}`, {});
      setPlugins(prev => prev.map(p => p.name === name ? { ...p, enabled: !current } : p));
    } finally { setToggling(null); }
  };

  const filtered = plugins.filter(p => {
    if (filter === 'enabled' && !p.enabled) return false;
    if (filter === 'disabled' && p.enabled) return false;
    if (search && !p.name.toLowerCase().includes(search.toLowerCase()) &&
      !p.description.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const grouped = filtered.reduce<Record<string, Plugin[]>>((acc, p) => {
    const cat = p.category || 'core';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(p);
    return acc;
  }, {});

  const enabledCount = plugins.filter(p => p.enabled).length;
  const errorCount = plugins.filter(p => p.status === 'error').length;

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', boxSizing: 'border-box', overflow: 'hidden' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Gestion des Plugins
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            {enabledCount}/{plugins.length} actifs
            {errorCount > 0 && <span style={{ color: 'var(--accent-red)', marginLeft: '0.5rem' }}>· {errorCount} en erreur</span>}
          </p>
        </div>
        <button onClick={loadPlugins} style={{
          padding: '0.5rem 0.875rem', borderRadius: '8px',
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.8125rem',
        }}>↻ Actualiser</button>
      </div>

      {/* Search + filters */}
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <span style={{
            position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)',
            color: 'var(--text-muted)', fontSize: '0.875rem',
          }}>🔍</span>
          <input
            type="text" placeholder="Rechercher un plugin..."
            value={search} onChange={e => setSearch(e.target.value)}
            style={{
              width: '100%', padding: '0.5rem 0.875rem 0.5rem 2.25rem',
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '8px', color: 'var(--text-primary)', fontSize: '0.875rem',
              outline: 'none', boxSizing: 'border-box',
            }}
          />
        </div>
        {(['all', 'enabled', 'disabled'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: '0.5rem 0.875rem', borderRadius: '8px',
              background: filter === f ? 'rgba(47,129,247,0.15)' : 'var(--bg-card)',
              border: `1px solid ${filter === f ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
              color: filter === f ? 'var(--accent-blue)' : 'var(--text-secondary)',
              cursor: 'pointer', fontSize: '0.8125rem',
            }}
          >
            {{ all: 'Tous', enabled: '✅ Actifs', disabled: '⭕ Inactifs' }[f]}
          </button>
        ))}
      </div>

      {/* Plugin grid by category */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '0.75rem' }}>
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} style={{ height: '100px', background: 'var(--bg-card)', borderRadius: '10px', animation: 'pulse 1.5s ease infinite' }} />
            ))}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {Object.entries(grouped).map(([category, catPlugins]) => {
              const catCfg = CATEGORY_CONFIG[category] || CATEGORY_CONFIG.core;
              return (
                <div key={category}>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: '0.625rem',
                    marginBottom: '0.75rem',
                  }}>
                    <span style={{ fontSize: '1rem' }}>{catCfg.icon}</span>
                    <span style={{ color: catCfg.color, fontWeight: 600, fontSize: '0.875rem', textTransform: 'capitalize' }}>
                      {category}
                    </span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      ({catPlugins.length})
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '0.625rem' }}>
                    {catPlugins.map(plugin => {
                      const statusCfg = STATUS_CONFIG[plugin.status || 'ok'];
                      const isToggling = toggling === plugin.name;
                      return (
                        <div
                          key={plugin.name}
                          style={{
                            background: 'var(--bg-card)',
                            border: `1px solid ${plugin.status === 'error' ? 'rgba(248,81,73,0.3)' : 'var(--border-color)'}`,
                            borderRadius: '10px', padding: '1rem',
                            display: 'flex', gap: '0.875rem', alignItems: 'flex-start',
                            opacity: plugin.enabled ? 1 : 0.65,
                            transition: 'opacity 0.2s',
                          }}
                        >
                          {/* Icon */}
                          <div style={{
                            width: '40px', height: '40px', borderRadius: '10px',
                            background: plugin.enabled ? `${catCfg.color}22` : 'var(--bg-tertiary)',
                            border: `1px solid ${plugin.enabled ? `${catCfg.color}44` : 'var(--border-color)'}`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: '1.125rem', flexShrink: 0,
                          }}>
                            {catCfg.icon}
                          </div>

                          {/* Info */}
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                              <div>
                                <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
                                  {plugin.name}
                                </div>
                                <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                                  v{plugin.version} · {plugin.routes_count || 0} routes
                                </div>
                              </div>
                              {/* Toggle */}
                              <button
                                onClick={() => toggle(plugin.name, plugin.enabled)}
                                disabled={isToggling}
                                style={{
                                  width: '40px', height: '22px', borderRadius: '11px',
                                  border: 'none', cursor: isToggling ? 'not-allowed' : 'pointer',
                                  background: plugin.enabled ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                                  position: 'relative', flexShrink: 0, transition: 'background 0.2s',
                                }}
                              >
                                <div style={{
                                  position: 'absolute', top: '3px',
                                  left: plugin.enabled ? '20px' : '3px',
                                  width: '16px', height: '16px', borderRadius: '50%',
                                  background: isToggling ? '#aaa' : '#fff',
                                  transition: 'left 0.2s',
                                  boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                                }} />
                              </button>
                            </div>

                            <p style={{
                              color: 'var(--text-secondary)', fontSize: '0.75rem',
                              margin: '0.375rem 0 0', lineHeight: 1.4,
                              display: '-webkit-box', WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical', overflow: 'hidden',
                            }}>
                              {plugin.description}
                            </p>

                            {/* Status */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', marginTop: '0.5rem' }}>
                              <span style={{ fontSize: '0.75rem' }}>{statusCfg.icon}</span>
                              <span style={{ color: statusCfg.color, fontSize: '0.7rem' }}>{statusCfg.label}</span>
                              {plugin.error && (
                                <span title={plugin.error} style={{ color: 'var(--accent-red)', fontSize: '0.7rem', cursor: 'help' }}>
                                  — {plugin.error.slice(0, 40)}...
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}
