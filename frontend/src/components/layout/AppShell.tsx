import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useState, useEffect } from 'react';

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard', '/prospects': 'Prospects', '/pipeline': 'Pipeline',
  '/analytics': 'Analytics', '/sourcing': 'Sourcing', '/table': 'Spreadsheet',
  '/signals': "Signaux d'affaires", '/sequencer': 'Séquences Email',
  '/inbound': 'Inbound Enrichment', '/contacts': 'Contact Intelligence',
  '/agent': 'Agent IA', '/webhooks': 'Webhooks', '/plugins': 'Plugins',
  '/settings': 'Paramètres', '/abm': 'ABM / TAM', '/crm-sync': 'CRM Sync',
};

export default function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const [commandOpen, setCommandOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const title = PAGE_TITLES[location.pathname] || 'B2B Prospector';

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  useEffect(() => { setSidebarOpen(false); }, [location.pathname]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); setCommandOpen(p => !p); }
      if (e.key === 'Escape') { setCommandOpen(false); setSidebarOpen(false); }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  const QUICK_LINKS = [
    { icon: '🏢', label: 'Prospects', href: '/prospects', shortcut: 'P' },
    { icon: '📊', label: 'Pipeline', href: '/pipeline', shortcut: 'K' },
    { icon: '📈', label: 'Analytics', href: '/analytics', shortcut: 'A' },
    { icon: '🔍', label: 'Sourcing', href: '/sourcing', shortcut: 'S' },
    { icon: '⚡', label: 'Signaux', href: '/signals', shortcut: 'G' },
    { icon: '🤖', label: 'Agent IA', href: '/agent', shortcut: 'I' },
    { icon: '🎯', label: 'ABM', href: '/abm', shortcut: 'M' },
    { icon: '🔄', label: 'CRM Sync', href: '/crm-sync', shortcut: 'C' },
    { icon: '📧', label: 'Séquences', href: '/sequencer', shortcut: 'E' },
    { icon: '⚙️', label: 'Paramètres', href: '/settings', shortcut: ',' },
  ];

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      {isMobile && sidebarOpen && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 49, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(2px)' }}
          onClick={() => setSidebarOpen(false)} />
      )}
      <div style={{
        position: isMobile ? 'fixed' : 'relative',
        left: isMobile ? (sidebarOpen ? '0' : '-240px') : '0',
        top: 0, bottom: 0, zIndex: isMobile ? 50 : 'auto' as any,
        transition: 'left 0.25s cubic-bezier(0.4,0,0.2,1)', flexShrink: 0,
      }}>
        <Sidebar />
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        <header style={{
          height: '48px', background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', padding: '0 1rem', flexShrink: 0, gap: '0.75rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {isMobile && (
              <button onClick={() => setSidebarOpen(true)} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--text-secondary)', padding: '4px',
                display: 'flex', flexDirection: 'column', gap: '4px',
              }}>
                {[0,1,2].map(i => <span key={i} style={{ width: '18px', height: '2px', background: 'currentColor', borderRadius: '1px', display: 'block' }} />)}
              </button>
            )}
            <span style={{ color: 'var(--text-primary)', fontSize: '0.9375rem', fontWeight: 600 }}>{title}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button onClick={() => setCommandOpen(true)} style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.3rem 0.625rem',
              background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
              borderRadius: '6px', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.8125rem',
            }}>
              <span>🔍</span>
              {!isMobile && <><span>Rechercher</span><kbd style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '4px', padding: '0 4px', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>⌘K</kbd></>}
            </button>
            <button style={{ width: '32px', height: '32px', borderRadius: '6px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', cursor: 'pointer', fontSize: '0.875rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>🔔</button>
          </div>
        </header>
        <main style={{ flex: 1, overflow: 'hidden' }}><Outlet /></main>
      </div>
      {commandOpen && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 3000, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '10vh 1rem' }}
          onClick={() => setCommandOpen(false)}>
          <div style={{ width: '600px', maxWidth: '95vw', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 24px 64px rgba(0,0,0,0.6)', animation: 'popIn 0.15s ease' }}
            onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.875rem 1rem', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>🔍</span>
              <input autoFocus placeholder="Naviguer, rechercher des prospects..." style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: 'var(--text-primary)', fontSize: '0.9375rem' }} />
              <kbd style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>Esc</kbd>
            </div>
            <div style={{ padding: '0.5rem' }}>
              <div style={{ padding: '0.375rem 0.75rem', fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.125rem' }}>Navigation rapide</div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '2px' }}>
                {QUICK_LINKS.map(item => (
                  <button key={item.href} onClick={() => { navigate(item.href); setCommandOpen(false); }}
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', padding: '0.625rem 0.75rem', borderRadius: '8px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '0.875rem', textAlign: 'left', width: '100%' }}
                    onMouseEnter={e => { const el = e.currentTarget as HTMLElement; el.style.background = 'var(--bg-secondary)'; el.style.color = 'var(--text-primary)'; }}
                    onMouseLeave={e => { const el = e.currentTarget as HTMLElement; el.style.background = 'none'; el.style.color = 'var(--text-secondary)'; }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}><span>{item.icon}</span><span>{item.label}</span></div>
                    {!isMobile && <kbd style={{ padding: '1px 6px', borderRadius: '4px', fontSize: '0.7rem', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>{item.shortcut}</kbd>}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
      <style>{`@keyframes popIn { from { opacity:0; transform:scale(0.96) translateY(-8px); } to { opacity:1; transform:scale(1) translateY(0); } } @keyframes spin { to { transform:rotate(360deg); } }`}</style>
    </div>
  );
}
