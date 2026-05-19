import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Search, Bell, ChevronDown, LogOut, Settings, User, Moon } from 'lucide-react';

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
  const [cmdOpen, setCmdOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const title = PAGE_TITLES[location.pathname] || 'B2B Prospector';

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  useEffect(() => { setSidebarOpen(false); setNotifOpen(false); setUserOpen(false); }, [location.pathname]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); setCmdOpen(p => !p); }
      if (e.key === 'Escape') { setCmdOpen(false); setNotifOpen(false); setUserOpen(false); }
    };
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, []);

  const initials = user?.email?.slice(0, 2).toUpperCase() || 'AD';
  const username = user?.email?.split('@')[0] || 'Admin';

  const LINKS = [
    { icon: '📊', label: 'Dashboard', href: '/' },
    { icon: '🏢', label: 'Prospects', href: '/prospects' },
    { icon: '🔀', label: 'Pipeline', href: '/pipeline' },
    { icon: '🔍', label: 'Scraping', href: '/sourcing' },
    { icon: '⚡', label: 'Signaux', href: '/signals' },
    { icon: '📧', label: 'Séquences', href: '/sequencer' },
    { icon: '🤖', label: 'Agent IA', href: '/agent' },
    { icon: '⚙️', label: 'Paramètres', href: '/settings' },
  ];

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)', overflow: 'hidden' }}>

      {isMobile && sidebarOpen && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 49, background: 'rgba(0,0,0,.3)' }}
          onClick={() => setSidebarOpen(false)} />
      )}

      <div style={{
        position: isMobile ? 'fixed' : 'relative',
        left: isMobile ? (sidebarOpen ? '0' : '-260px') : '0',
        top: 0, bottom: 0, zIndex: isMobile ? 50 : 'auto' as any,
        transition: 'left .25s ease', flexShrink: 0,
      }}>
        <Sidebar />
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>

        {/* ── Header CRMi exact ── */}
        <header style={{
          height: 'var(--header-height)',
          background: '#fff',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 1.5rem', flexShrink: 0,
          boxShadow: '0 1px 4px rgba(0,0,0,.05)', gap: '1rem',
        }}>

          {/* Left: hamburger + breadcrumb */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '.875rem' }}>
            {isMobile && (
              <button onClick={() => setSidebarOpen(true)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {[0,1,2].map(i => <span key={i} style={{ width: 18, height: 2, background: 'var(--text-secondary)', borderRadius: 1, display: 'block' }} />)}
              </button>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '.875rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>B2B Prospector</span>
              <span style={{ color: 'var(--border-color)' }}>/</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{title}</span>
            </div>
          </div>

          {/* Right: search + actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>

            {/* Search bar */}
            <button
              onClick={() => setCmdOpen(true)}
              style={{
                display: 'flex', alignItems: 'center', gap: '.5rem',
                padding: '.375rem .875rem',
                background: '#f0f4ff', border: '1px solid var(--border-color)',
                borderRadius: 8, cursor: 'pointer', color: 'var(--text-muted)',
                fontSize: '.8125rem', transition: 'all .15s',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = '#0d6efd'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)'; }}
            >
              <Search size={14} />
              {!isMobile && <><span>Rechercher...</span><kbd style={{ background: '#fff', border: '1px solid var(--border-color)', borderRadius: 4, padding: '1px 5px', fontSize: '.6875rem', boxShadow: '0 1px 2px rgba(0,0,0,.05)' }}>⌘K</kbd></>}
            </button>

            {/* Notifications */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => { setNotifOpen(o => !o); setUserOpen(false); }}
                style={{
                  width: 36, height: 36, borderRadius: 8,
                  background: '#f0f4ff', border: '1px solid var(--border-color)',
                  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  position: 'relative', transition: 'all .15s',
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#e8eeff'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = '#f0f4ff'; }}
              >
                <Bell size={16} color="var(--text-secondary)" />
                <span style={{ position: 'absolute', top: 6, right: 7, width: 8, height: 8, borderRadius: '50%', background: '#dc3545', border: '2px solid #fff' }} />
              </button>

              {notifOpen && (
                <div style={{
                  position: 'absolute', top: 44, right: 0, width: 320,
                  background: '#fff', border: '1px solid var(--border-color)',
                  borderRadius: 10, boxShadow: 'var(--shadow-lg)', zIndex: 200,
                }}>
                  <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>Notifications</span>
                    <button style={{ background: 'none', border: 'none', color: '#0d6efd', fontSize: '.8125rem', cursor: 'pointer' }}>Tout lire</button>
                  </div>
                  {[
                    { icon: '🔍', text: 'Scraping terminé — 25 prospects', time: 'Il y a 5 min', unread: true },
                    { icon: '⚡', text: '3 nouveaux signaux détectés', time: 'Il y a 12 min', unread: true },
                    { icon: '📧', text: '5 emails envoyés via séquence', time: 'Il y a 1h', unread: false },
                  ].map((n, i) => (
                    <div key={i}
                      style={{ padding: '.875rem 1.25rem', display: 'flex', gap: '.75rem', borderBottom: '1px solid #f8f9fc', cursor: 'pointer', background: n.unread ? 'rgba(13,110,253,.03)' : 'transparent', transition: 'background .1s' }}
                      onMouseEnter={e => (e.currentTarget.style.background = '#f8f9fc')}
                      onMouseLeave={e => (e.currentTarget.style.background = n.unread ? 'rgba(13,110,253,.03)' : 'transparent')}
                    >
                      <span style={{ fontSize: '1.25rem', flexShrink: 0 }}>{n.icon}</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <p style={{ margin: 0, fontSize: '.8125rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>{n.text}</p>
                        <span style={{ fontSize: '.75rem', color: 'var(--text-muted)' }}>{n.time}</span>
                      </div>
                      {n.unread && <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#0d6efd', flexShrink: 0, marginTop: 4 }} />}
                    </div>
                  ))}
                  <div style={{ padding: '.75rem', textAlign: 'center' }}>
                    <button style={{ background: 'none', border: 'none', color: '#0d6efd', fontSize: '.8125rem', cursor: 'pointer', fontWeight: 500 }}>Voir toutes</button>
                  </div>
                </div>
              )}
            </div>

            {/* User dropdown */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => { setUserOpen(o => !o); setNotifOpen(false); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: '.5rem',
                  padding: '.25rem .625rem .25rem .25rem',
                  background: '#f0f4ff', border: '1px solid var(--border-color)',
                  borderRadius: 8, cursor: 'pointer', transition: 'all .15s',
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#e8eeff'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = '#f0f4ff'; }}
              >
                <div style={{
                  width: 30, height: 30, borderRadius: 6,
                  background: 'var(--grad-purple)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontWeight: 700, fontSize: '.75rem',
                }}>{initials}</div>
                {!isMobile && (
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontSize: '.8125rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>{username}</div>
                    <div style={{ fontSize: '.7rem', color: 'var(--text-muted)' }}>Admin</div>
                  </div>
                )}
                <ChevronDown size={12} color="var(--text-muted)" />
              </button>

              {userOpen && (
                <div style={{
                  position: 'absolute', top: 44, right: 0, width: 200,
                  background: '#fff', border: '1px solid var(--border-color)',
                  borderRadius: 10, boxShadow: 'var(--shadow-lg)', zIndex: 200, overflow: 'hidden',
                }}>
                  <div style={{ padding: '.875rem 1rem', borderBottom: '1px solid var(--border-color)' }}>
                    <div style={{ fontWeight: 600, fontSize: '.875rem', color: 'var(--text-primary)' }}>{username}</div>
                    <div style={{ fontSize: '.75rem', color: 'var(--text-muted)' }}>{user?.email}</div>
                  </div>
                  {[
                    { icon: <User size={14} />, label: 'Profil', action: () => {} },
                    { icon: <Settings size={14} />, label: 'Paramètres', action: () => navigate('/settings') },
                  ].map(item => (
                    <button key={item.label} onClick={item.action}
                      style={{ display: 'flex', alignItems: 'center', gap: '.625rem', width: '100%', padding: '.625rem 1rem', background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '.875rem', cursor: 'pointer', transition: 'background .1s' }}
                      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#f0f4ff'; }}
                      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'none'; }}
                    >
                      {item.icon}{item.label}
                    </button>
                  ))}
                  <div style={{ borderTop: '1px solid var(--border-color)' }}>
                    <button onClick={logout}
                      style={{ display: 'flex', alignItems: 'center', gap: '.625rem', width: '100%', padding: '.625rem 1rem', background: 'none', border: 'none', color: '#dc3545', fontSize: '.875rem', cursor: 'pointer', transition: 'background .1s' }}
                      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(220,53,69,.05)'; }}
                      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'none'; }}
                    >
                      <LogOut size={14} /> Se déconnecter
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        <main style={{ flex: 1, overflow: 'hidden' }}><Outlet /></main>
      </div>

      {/* Command palette */}
      {cmdOpen && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 3000, background: 'rgba(0,0,0,.4)', backdropFilter: 'blur(3px)', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '10vh 1rem' }}
          onClick={() => setCmdOpen(false)}>
          <div style={{ width: 560, maxWidth: '95vw', background: '#fff', border: '1px solid var(--border-color)', borderRadius: 12, overflow: 'hidden', boxShadow: 'var(--shadow-xl)', animation: 'popIn .15s ease' }}
            onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem', padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-color)' }}>
              <Search size={16} color="var(--text-muted)" />
              <input autoFocus placeholder="Rechercher ou naviguer..."
                style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: 'var(--text-primary)', fontSize: '.9375rem', padding: 0 }} />
              <kbd style={{ padding: '2px 7px', borderRadius: 5, fontSize: '.75rem', background: '#f0f4ff', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>Esc</kbd>
            </div>
            <div style={{ padding: '.5rem' }}>
              <div style={{ padding: '.375rem .75rem', fontSize: '.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: '.25rem', fontWeight: 700 }}>
                Navigation rapide
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 2 }}>
                {LINKS.map(item => (
                  <button key={item.href}
                    onClick={() => { navigate(item.href); setCmdOpen(false); }}
                    style={{ display: 'flex', alignItems: 'center', gap: '.75rem', padding: '.625rem .75rem', borderRadius: 8, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '.875rem', textAlign: 'left', width: '100%', transition: 'all .1s' }}
                    onMouseEnter={e => { const el = e.currentTarget as HTMLElement; el.style.background = '#f0f4ff'; el.style.color = '#0d6efd'; }}
                    onMouseLeave={e => { const el = e.currentTarget as HTMLElement; el.style.background = 'none'; el.style.color = 'var(--text-secondary)'; }}
                  >
                    <span>{item.icon}</span><span>{item.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes popIn { from{opacity:0;transform:scale(.96) translateY(-6px)} to{opacity:1;transform:scale(1) translateY(0)} }
        @keyframes spin  { to{transform:rotate(360deg)} }
      `}</style>
    </div>
  );
}
