import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Workflow, Users, BarChart2,
  Puzzle, Settings, ChevronRight
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard',       href: '/',          icon: LayoutDashboard },
  { name: 'Pipeline Kanban', href: '/pipeline',   icon: Workflow },
  { name: 'Prospects',       href: '/prospects',  icon: Users },
  { name: 'Analytics',       href: '/analytics',  icon: BarChart2 },
  { name: 'Plugins',         href: '/plugins',    icon: Puzzle },
  { name: 'Paramètres',      href: '/settings',   icon: Settings },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside style={{
      width: '220px', height: '100vh',
      background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex', flexDirection: 'column',
      flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{
        padding: '1.25rem 1rem',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex', alignItems: 'center', gap: '0.625rem',
      }}>
        <div style={{
          width: '28px', height: '28px', borderRadius: '7px',
          background: 'linear-gradient(135deg, var(--accent-blue), #7c3aed)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.875rem', flexShrink: 0,
        }}>⚡</div>
        <span style={{
          fontSize: '0.9375rem', fontWeight: 700,
          color: 'var(--text-primary)', letterSpacing: '-0.02em',
        }}>Prospector</span>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '0.5rem', overflowY: 'auto' }}>
        {navigation.map(({ name, href, icon: Icon }) => {
          const active = location.pathname === href;
          return (
            <Link key={href} to={href} style={{
              display: 'flex', alignItems: 'center', gap: '0.625rem',
              padding: '0.5rem 0.75rem', borderRadius: '7px',
              marginBottom: '2px', textDecoration: 'none',
              color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: active ? 'var(--bg-tertiary)' : 'transparent',
              fontSize: '0.875rem', fontWeight: active ? 600 : 400,
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.background = 'var(--bg-hover)'; }}
            onMouseLeave={e => { if (!active) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
            >
              <Icon size={16} strokeWidth={active ? 2.5 : 1.75} />
              <span style={{ flex: 1 }}>{name}</span>
              {active && <ChevronRight size={12} style={{ opacity: 0.4 }} />}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '0.75rem 1rem',
        borderTop: '1px solid var(--border-color)',
        fontSize: '0.75rem', color: 'var(--text-muted)',
      }}>
        B2B Prospector v4.0
      </div>
    </aside>
  );
}
