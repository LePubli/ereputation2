import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useState, useEffect } from 'react';

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/prospects': 'Prospects',
  '/pipeline': 'Pipeline',
  '/analytics': 'Analytics',
  '/sourcing': 'Sourcing',
  '/table': 'Spreadsheet',
  '/signals': "Signaux d'affaires",
  '/sequencer': 'Séquences Email',
  '/inbound': 'Inbound Enrichment',
  '/contacts': 'Contact Intelligence',
  '/agent': 'Agent IA',
  '/webhooks': 'Webhooks',
  '/plugins': 'Plugins',
  '/settings': 'Paramètres',
  '/abm': 'ABM / TAM',
  '/crm-sync': 'CRM Sync',
};

export default function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const [commandOpen, setCommandOpen] = useState(false);
  const title = PAGE_TITLES[location.pathname] || 'B2B Prospector';

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandOpen(prev => !prev);
      }
      if (e.key === 'Escape') setCommandOpen(false);
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  const QUICK_LINKS = [
    { icon: '🏢', label: 'Prospects', href: '/prospects' },
    { icon: '📊', label: 'Pipeline', href: '/pipeline' },
    { icon: '📈', label: 'Analytics', href: '/analytics' },
    { icon: '🔍', label: 'Sourcing', href: '/sourcing' },
    { icon: '⚡', label: 'Signaux', href: '/signals' },
    { icon: '🤖', label: 'Agent IA', href: '/agent' },
    { icon: '📧', label: 'Séquences', href: '/sequencer' },
    { icon: '⚙️', label: 'Paramètres', href: '/settings' },
  ];

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      <Sidebar />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        {/* Topbar */}
        <header style={{
          height: '48px', background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', padding: '0 1.25rem',
          flexShrink: 0, gap: '1rem',
        }}>
          <span style={{ color: 'var(--text-primary)', fontSize: '0.9375rem', fontWeight: 600 }}>
            {title}
          </span>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              onClick={() => setCommandOpen(true)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.3rem 0.75rem',
                background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                borderRadius: '6px', cursor: 'pointer', color: 'var(--text-muted)',
                fontSize: '0.8125rem',
              }}
            >
              <span>🔍</span>
              <span>Rechercher</span>
              <kbd style={{
                background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                borderRadius: '4px', padding: '0 4px', fontSize: '0.6875rem',
                color: 'var(--text-muted)',
              }}>⌘K</kbd>
            </button>

            <button style={{
              width: '32px', height: '32px', borderRadius: '6px',
              background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
              cursor: 'pointer', fontSize: '0.875rem',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>🔔</button>
          </div>
        </header>

        {/* Page content */}
        <main style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
          <Outlet />
        </main>
      </div>

      {/* Command Palette */}
      {commandOpen && (
        <div
          style={{
            position: 'fixed', inset: 0, zIndex: 3000,
            background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
            padding: '10vh 1rem',
          }}
          onClick={() => setCommandOpen(false)}
        >
          <div
            style={{
              width: '600px', maxWidth: '95vw',
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '12px', overflow: 'hidden',
              boxShadow: '0 24px 64px rgba(0,0,0,0.6)',
              animation: 'popIn 0.15s ease',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{
              display: 'flex', alignItems: 'center', gap: '0.75rem',
              padding: '0.875rem 1rem', borderBottom: '1px solid var(--border-color)',
            }}>
              <span style={{ color: 'var(--text-muted)' }}>🔍</span>
              <input
                autoFocus
                placeholder="Naviguer, rechercher des prospects..."
                style={{
                  flex: 1, background: 'none', border: 'none', outline: 'none',
                  color: 'var(--text-primary)', fontSize: '0.9375rem',
                }}
              />
              <kbd style={{
                padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem',
                background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                color: 'var(--text-muted)',
              }}>Esc</kbd>
            </div>

            <div style={{ padding: '0.5rem' }}>
              <div style={{ padding: '0.375rem 0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Navigation rapide
              </div>
              {QUICK_LINKS.map(item => (
                <button
                  key={item.href}
                  onClick={() => { navigate(item.href); setCommandOpen(false); }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: '0.75rem',
                    padding: '0.625rem 0.75rem', borderRadius: '8px',
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--text-secondary)', fontSize: '0.875rem', textAlign: 'left',
                    transition: 'all 0.1s',
                  }}
                  onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-secondary)'; (e.currentTarget as HTMLElement).style.color = 'var(--text-primary)'; }}
                  onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'none'; (e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)'; }}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes popIn { from { opacity: 0; transform: scale(0.96) translateY(-8px); } to { opacity: 1; transform: scale(1) translateY(0); } }`}</style>
    </div>
  );
}
