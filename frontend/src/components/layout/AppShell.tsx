import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard', '/prospects': 'Prospects', '/pipeline': 'Pipeline',
  '/analytics': 'Analytics', '/sourcing': 'Sourcing', '/table': 'Spreadsheet',
  '/signals': "Signaux d'affaires", '/sequencer': 'Séquences Email',
  '/inbound': 'Inbound', '/contacts': 'Contact Intelligence',
  '/agent': 'Agent IA', '/webhooks': 'Webhooks', '/plugins': 'Plugins',
  '/settings': 'Paramètres', '/abm': 'ABM / TAM', '/crm-sync': 'CRM Sync',
};

export default function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [commandOpen, setCommandOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const title = PAGE_TITLES[location.pathname] || 'B2B Prospector';

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  useEffect(() => { setSidebarOpen(false); setNotifOpen(false); }, [location.pathname]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); setCommandOpen(p => !p); }
      if (e.key === 'Escape') { setCommandOpen(false); setSidebarOpen(false); setNotifOpen(false); }
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
    { icon: '🎯', label: 'ABM', href: '/abm' },
    { icon: '📧', label: 'Séquences', href: '/sequencer' },
    { icon: '🔄', label: 'CRM Sync', href: '/crm-sync' },
    { icon: '⚙️', label: 'Paramètres', href: '/settings' },
  ];

  const initials = user?.email?.slice(0, 2).toUpperCase() || 'AD';

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)', overflow: 'hidden' }}>

      {/* Mobile overlay */}
      {isMobile && sidebarOpen && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 49, background: 'rgba(30,42,59,0.4)', backdropFilter: 'blur(2px)' }}
          onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <div style={{
        position: isMobile ? 'fixed' : 'relative',
        left: isMobile ? (sidebarOpen ? '0' : '-260px') : '0',
        top: 0, bottom: 0, zIndex: isMobile ? 50 : 'auto' as any,
        transition: 'left 0.25s cubic-bezier(0.4,0,0.2,1)', flexShrink: 0,
      }}>
        <Sidebar />
      </div>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>

        {/* TopBar */}
        <header style={{
          height: 'var(--header-height)',
          background: 'var(--header-bg)',
          borderBottom: '1px solid var(--header-border)',
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 1.5rem', flexShrink: 0,
          boxShadow: '0 1px 4px rgba(30,42,59,0.05)',
        }}>
          {/* Left */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {isMobile && (
              <button onClick={() => setSidebarOpen(true)} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--text-secondary)', padding: '4px',
                display: 'flex', flexDirection: 'column', gap: '4px',
              }}>
                {[0,1,2].map(i => <span key={i} style={{ width: '18px', height: '2px', background: 'currentColor', borderRadius: '1px', display: 'block' }} />)}
              </button>
            )}
            {/* Breadcrumb style title */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>B2B Prospector</span>
              <span style={{ color: 'var(--border-color)', fontSize: '0.875rem' }}>/</span>
              <span style={{ color: 'var(--text-primary)', fontSize: '0.875rem', fontWeight: 600 }}>{title}</span>
            </div>
          </div>

          {/* Right */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>

            {/* Search */}
            <button
              onClick={() => setCommandOpen(true)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.375rem 0.875rem',
                background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                borderRadius: '8px', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.8125rem',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--accent-blue)')}
              onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border-color)')}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
              {!isMobile && (
                <>
                  <span>Rechercher...</span>
                  <kbd style={{ background: '#fff', border: '1px solid var(--border-color)', borderRadius: '4px', padding: '1px 5px', fontSize: '0.6875rem', color: 'var(--text-muted)', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>⌘K</kbd>
                </>
              )}
            </button>

            {/* Notifications */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setNotifOpen(o => !o)}
                style={{
                  width: '36px', height: '36px', borderRadius: '8px',
                  background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                  cursor: 'pointer', fontSize: '1rem', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', position: 'relative',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#fff'; (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent-blue)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-tertiary)'; (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)'; }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                </svg>
                <span style={{ position: 'absolute', top: '6px', right: '6px', width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-red)', border: '2px solid #fff' }} />
              </button>

              {notifOpen && (
                <div style={{
                  position: 'absolute', top: '44px', right: 0, width: '320px',
                  background: '#fff', border: '1px solid var(--border-color)',
                  borderRadius: '12px', boxShadow: 'var(--shadow-lg)',
                  zIndex: 200, overflow: 'hidden',
                }}>
                  <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>Notifications</span>
                    <button style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', fontSize: '0.8125rem', cursor: 'pointer', padding: 0 }}>Tout marquer lu</button>
                  </div>
                  {[
                    { icon: '🔍', text: 'Nouveau scraping terminé — 25 prospects', time: 'Il y a 5 min', dot: true },
                    { icon: '⚡', text: '3 nouveaux signaux détectés', time: 'Il y a 12 min', dot: true },
                    { icon: '📧', text: 'Séquence "PME Nord" — 5 emails envoyés', time: 'Il y a 1h', dot: false },
                  ].map((n, i) => (
                    <div key={i} style={{ padding: '0.875rem 1.25rem', display: 'flex', gap: '0.75rem', alignItems: 'flex-start', borderBottom: '1px solid #f8f9fc', cursor: 'pointer', transition: 'background 0.1s' }}
                      onMouseEnter={e => (e.currentTarget.style.background = '#f8fafc')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                      <span style={{ fontSize: '1.25rem', flexShrink: 0 }}>{n.icon}</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>{n.text}</p>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{n.time}</span>
                      </div>
                      {n.dot && <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-blue)', flexShrink: 0, marginTop: '4px' }} />}
                    </div>
                  ))}
                  <div style={{ padding: '0.75rem 1.25rem', textAlign: 'center' }}>
                    <button style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', fontSize: '0.8125rem', cursor: 'pointer' }}>Voir toutes les notifications</button>
                  </div>
                </div>
              )}
            </div>

            {/* User avatar */}
            <div style={{ position: 'relative' }}>
              <button style={{
                display: 'flex', alignItems: 'center', gap: '0.625rem',
                padding: '0.25rem 0.5rem 0.25rem 0.25rem',
                background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                borderRadius: '8px', cursor: 'pointer', transition: 'all 0.15s',
              }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#fff'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-tertiary)'; }}
                onClick={logout}
                title="Se déconnecter"
              >
                <div style={{
                  width: '28px', height: '28px', borderRadius: '6px',
                  background: 'linear-gradient(135deg, #3468f6, #7c4dff)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontWeight: 700, fontSize: '0.75rem',
                }}>
                  {initials}
                </div>
                {!isMobile && (
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                      {user?.email?.split('@')[0] || 'Admin'}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', lineHeight: 1.2 }}>Administrateur</div>
                  </div>
                )}
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2.5">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <main style={{ flex: 1, overflow: 'hidden' }}><Outlet /></main>
      </div>

      {/* Command palette */}
      {commandOpen && (
        <div
          style={{ position: 'fixed', inset: 0, zIndex: 3000, background: 'rgba(30,42,59,0.5)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '10vh 1rem' }}
          onClick={() => setCommandOpen(false)}
        >
          <div style={{ width: '580px', maxWidth: '95vw', background: '#fff', border: '1px solid var(--border-color)', borderRadius: '14px', overflow: 'hidden', boxShadow: 'var(--shadow-xl)', animation: 'popIn 0.15s ease' }}
            onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-color)' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2.5">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
              <input autoFocus placeholder="Rechercher ou naviguer..."
                style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: 'var(--text-primary)', fontSize: '0.9375rem', padding: 0 }} />
              <kbd style={{ padding: '2px 7px', borderRadius: '5px', fontSize: '0.75rem', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', color: 'var(--text-muted)', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>Esc</kbd>
            </div>
            <div style={{ padding: '0.5rem' }}>
              <div style={{ padding: '0.375rem 0.75rem', fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.25rem', fontWeight: 600 }}>Navigation rapide</div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '2px' }}>
                {QUICK_LINKS.map(item => (
                  <button key={item.href}
                    onClick={() => { navigate(item.href); setCommandOpen(false); }}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.625rem 0.75rem', borderRadius: '8px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '0.875rem', textAlign: 'left', width: '100%', transition: 'all 0.1s' }}
                    onMouseEnter={e => { const el = e.currentTarget as HTMLElement; el.style.background = 'var(--bg-hover)'; el.style.color = 'var(--accent-blue)'; }}
                    onMouseLeave={e => { const el = e.currentTarget as HTMLElement; el.style.background = 'none'; el.style.color = 'var(--text-secondary)'; }}
                  >
                    <span style={{ fontSize: '1rem' }}>{item.icon}</span>
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes popIn { from { opacity:0; transform:scale(0.96) translateY(-6px); } to { opacity:1; transform:scale(1) translateY(0); } }
        @keyframes spin { to { transform:rotate(360deg); } }
      `}</style>
    </div>
  );
}
