import { NavLink } from 'react-router-dom';

interface NavItem { to: string; icon: string; label: string; }
interface NavSection { label: string; items: NavItem[]; }

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
  return (
    <aside style={{
      width: 'var(--sidebar-width)',
      minWidth: 'var(--sidebar-width)',
      height: '100vh',
      background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      boxShadow: '1px 0 8px rgba(30,42,59,0.04)',
    }}>

      {/* Logo */}
      <div style={{
        height: 'var(--header-height)',
        display: 'flex', alignItems: 'center',
        padding: '0 1.25rem',
        borderBottom: '1px solid var(--border-color)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '8px',
            background: 'linear-gradient(135deg, #3468f6, #7c4dff)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 800, fontSize: '0.875rem',
            boxShadow: '0 4px 12px rgba(52,104,246,0.35)',
          }}>B</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--text-primary)', lineHeight: 1.2 }}>B2B Prospector</div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', lineHeight: 1 }}>CRM & Sourcing</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '0.75rem 0.75rem' }}>
        {NAV_SECTIONS.map(section => (
          <div key={section.label} style={{ marginBottom: '0.25rem' }}>
            <div style={{
              fontSize: '0.6875rem', fontWeight: 700,
              color: 'var(--text-muted)',
              textTransform: 'uppercase', letterSpacing: '0.07em',
              padding: '0.625rem 0.875rem 0.375rem',
            }}>
              {section.label}
            </div>
            {section.items.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                style={({ isActive }) => ({
                  display: 'flex', alignItems: 'center', gap: '0.625rem',
                  padding: '0.5625rem 0.875rem', borderRadius: '8px',
                  color: isActive ? 'var(--accent-blue)' : 'var(--text-secondary)',
                  background: isActive ? 'var(--sidebar-active-bg)' : 'transparent',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  transition: 'all 0.15s',
                  marginBottom: '2px',
                  borderLeft: isActive ? '3px solid var(--accent-blue)' : '3px solid transparent',
                })}
                onMouseEnter={e => {
                  const el = e.currentTarget as HTMLElement;
                  if (!el.style.background.includes('0.08')) {
                    el.style.background = 'var(--bg-hover)';
                    el.style.color = 'var(--accent-blue)';
                  }
                }}
                onMouseLeave={e => {
                  const el = e.currentTarget as HTMLElement;
                  if (!el.style.background.includes('0.08')) {
                    el.style.background = 'transparent';
                    el.style.color = 'var(--text-secondary)';
                  }
                }}
              >
                <span style={{ fontSize: '0.9375rem', width: '18px', textAlign: 'center', flexShrink: 0 }}>
                  {item.icon}
                </span>
                <span style={{ flex: 1 }}>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '0.875rem 1rem',
        borderTop: '1px solid var(--border-color)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.375rem', borderRadius: '8px' }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '8px',
            background: 'linear-gradient(135deg, #3468f6, #7c4dff)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 700, fontSize: '0.8125rem', flexShrink: 0,
          }}>AD</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              Admin
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Administrateur</div>
          </div>
          <div style={{
            width: '8px', height: '8px', borderRadius: '50%',
            background: 'var(--accent-green)',
            boxShadow: '0 0 0 2px rgba(27,193,94,0.2)',
          }} />
        </div>
      </div>
    </aside>
  );
}
