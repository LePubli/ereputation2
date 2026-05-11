import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface NavItem {
  to: string;
  icon: string;
  label: string;
  badge?: string | number;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    label: 'Principal',
    items: [
      { to: '/', icon: '⚡', label: 'Dashboard' },
      { to: '/prospects', icon: '🏢', label: 'Prospects' },
      { to: '/pipeline', icon: '📊', label: 'Pipeline' },
      { to: '/analytics', icon: '📈', label: 'Analytics' },
    ],
  },
  {
    label: 'Sourcing',
    items: [
      { to: '/sourcing', icon: '🔍', label: 'Scraping' },
      { to: '/table', icon: '📋', label: 'Spreadsheet' },
      { to: '/signals', icon: '🔔', label: 'Signaux' },
    ],
  },
  {
    label: 'Marketing & Sales',
    items: [
      { to: '/sequencer', icon: '📧', label: 'Séquences Email' },
      { to: '/inbound', icon: '📥', label: 'Inbound' },
      { to: '/abm', icon: '🎯', label: 'ABM / TAM' },
      { to: '/crm-sync', icon: '🔄', label: 'CRM Sync' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { to: '/agent', icon: '🤖', label: 'Agent IA' },
      { to: '/contacts', icon: '👤', label: 'Contacts' },
    ],
  },
  {
    label: 'Système',
    items: [
      { to: '/webhooks', icon: '🔗', label: 'Webhooks' },
      { to: '/plugins', icon: '🧩', label: 'Plugins' },
      { to: '/settings', icon: '⚙️', label: 'Paramètres' },
    ],
  },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside style={{
      width: '220px',
      minWidth: '220px',
      height: '100vh',
      background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Logo */}
      <div style={{
        padding: '1.25rem 1rem',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.625rem',
        flexShrink: 0,
      }}>
        <div style={{
          width: '32px', height: '32px', borderRadius: '8px',
          background: 'linear-gradient(135deg, var(--accent-blue), #7c3aed)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '1rem', flexShrink: 0,
        }}>⚡</div>
        <div>
          <div style={{
            fontSize: '0.875rem', fontWeight: 700,
            color: 'var(--text-primary)', lineHeight: 1.2,
          }}>B2B Prospector</div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Le Publicitaire</div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '0.75rem 0.5rem', scrollbarWidth: 'thin' }}>
        {NAV_SECTIONS.map(section => (
          <div key={section.label} style={{ marginBottom: '1rem' }}>
            {/* Section label */}
            <div style={{
              padding: '0.25rem 0.625rem',
              fontSize: '0.625rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: 'var(--text-muted)',
              marginBottom: '0.25rem',
            }}>
              {section.label}
            </div>

            {/* Items */}
            {section.items.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.4375rem 0.625rem',
                  borderRadius: '6px',
                  textDecoration: 'none',
                  fontSize: '0.8125rem',
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background: isActive ? 'rgba(47,129,247,0.12)' : 'transparent',
                  marginBottom: '1px',
                  transition: 'all 0.1s',
                  position: 'relative' as const,
                })}
                onMouseEnter={e => {
                  const el = e.currentTarget as HTMLElement;
                  if (!el.style.background.includes('rgba(47')) {
                    el.style.background = 'rgba(255,255,255,0.05)';
                    el.style.color = 'var(--text-primary)';
                  }
                }}
                onMouseLeave={e => {
                  const el = e.currentTarget as HTMLElement;
                  if (!el.style.background.includes('rgba(47')) {
                    el.style.background = 'transparent';
                    el.style.color = 'var(--text-secondary)';
                  }
                }}
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <div style={{
                        position: 'absolute',
                        left: 0, top: '4px', bottom: '4px',
                        width: '3px', borderRadius: '0 2px 2px 0',
                        background: 'var(--accent-blue)',
                      }} />
                    )}
                    <span style={{ fontSize: '0.875rem', flexShrink: 0 }}>{item.icon}</span>
                    <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {item.label}
                    </span>
                    {item.badge !== undefined && (
                      <span style={{
                        background: 'var(--accent-blue)',
                        color: '#fff', borderRadius: '10px',
                        padding: '0 5px', fontSize: '0.625rem', fontWeight: 700,
                        flexShrink: 0,
                      }}>
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* User footer */}
      <div style={{
        padding: '0.875rem 0.75rem',
        borderTop: '1px solid var(--border-color)',
        flexShrink: 0,
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.625rem',
          padding: '0.5rem', borderRadius: '8px',
          cursor: 'pointer', transition: 'background 0.1s',
        }}
          onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.05)'}
          onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = 'transparent'}
        >
          {/* Avatar */}
          <div style={{
            width: '30px', height: '30px', borderRadius: '50%',
            background: 'linear-gradient(135deg, #2f81f7, #7c3aed)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.75rem', fontWeight: 700, color: '#fff', flexShrink: 0,
          }}>
            {user?.email?.slice(0, 1).toUpperCase() || 'A'}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>
              {user?.email?.split('@')[0] || 'Admin'}
            </div>
            <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>Administrateur</div>
          </div>
          <button
            onClick={handleLogout}
            title="Déconnexion"
            style={{
              background: 'none', border: 'none',
              color: 'var(--text-muted)', cursor: 'pointer',
              fontSize: '0.875rem', padding: '0.25rem', borderRadius: '4px',
              flexShrink: 0,
            }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.color = 'var(--accent-red)'}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)'}
          >
            ⏻
          </button>
        </div>
      </div>

      <style>{`
        aside nav::-webkit-scrollbar { width: 4px; }
        aside nav::-webkit-scrollbar-track { background: transparent; }
        aside nav::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 2px; }
      `}</style>
    </aside>
  );
}
