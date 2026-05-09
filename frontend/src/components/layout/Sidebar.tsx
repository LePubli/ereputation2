import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Table2, Workflow, Users, Puzzle,
  Settings as SettingsIcon, LogOut, Sparkles, Webhook,
  Mail, Bell, ArrowDownToLine, Target, RefreshCw
} from 'lucide-react';
import { useAuthStore } from '../../hooks/useAuth';

const NAV_MAIN = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { to: '/table', label: 'Spreadsheet', icon: Table2, exact: false },
  { to: '/pipeline', label: 'Pipeline', icon: Workflow, exact: false },
  { to: '/prospects', label: 'Prospects', icon: Users, exact: false },
];

const NAV_MARKETING = [
  { to: '/signals', label: 'Signals', icon: Bell, exact: false },
  { to: '/inbound', label: 'Inbound', icon: ArrowDownToLine, exact: false },
  { to: '/abm', label: 'ABM / TAM', icon: Target, exact: false },
];

const NAV_SALES = [
  { to: '/agent', label: 'AI Agent', icon: Sparkles, exact: false },
  { to: '/sequences', label: 'Séquences', icon: Mail, exact: false },
  { to: '/crm', label: 'CRM Sync', icon: RefreshCw, exact: false },
];

const NAV_SYSTEM = [
  { to: '/webhooks', label: 'Webhooks', icon: Webhook, exact: false },
  { to: '/plugins', label: 'Plugins', icon: Puzzle, exact: false },
  { to: '/settings', label: 'Paramètres', icon: SettingsIcon, exact: false },
];

export function Sidebar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const appName = import.meta.env.VITE_APP_NAME ?? 'B2B Prospector';

  return (
    <aside
      style={{ background: 'var(--sidebar-bg)', color: 'var(--sidebar-text)', borderRight: '1px solid var(--sidebar-border)' }}
      className="w-56 flex flex-col h-screen sticky top-0 flex-shrink-0"
    >
      {/* Logo */}
      <div className="px-4 py-4" style={{ borderBottom: '1px solid var(--sidebar-border)' }}>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-blue-600 rounded text-white flex items-center justify-center font-bold text-xs flex-shrink-0">BP</div>
          <div>
            <div className="font-semibold text-sm" style={{ color: 'var(--sidebar-text)' }}>{appName}</div>
            <div className="text-xs" style={{ color: 'var(--sidebar-muted)' }}>GTM Platform</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        <NavSection label="Général" items={NAV_MAIN} />
        <NavSection label="Marketing" items={NAV_MARKETING} />
        <NavSection label="Sales" items={NAV_SALES} />
        <NavSection label="Système" items={NAV_SYSTEM} />
      </nav>

      {/* User footer */}
      <div className="px-3 py-3" style={{ borderTop: '1px solid var(--sidebar-border)' }}>
        {user && (
          <div className="mb-2 px-1">
            <div className="text-xs font-medium truncate" style={{ color: 'var(--sidebar-text)' }}>{user.full_name}</div>
            <div className="text-xs truncate" style={{ color: 'var(--sidebar-muted)' }}>{user.email}</div>
          </div>
        )}
        <button
          onClick={async () => { await logout(); navigate('/login'); }}
          className="flex items-center gap-2 w-full px-2 py-1.5 text-xs rounded transition"
          style={{ color: '#ef4444' }}
          onMouseEnter={e => (e.currentTarget.style.background = 'rgba(239,68,68,0.1)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
        >
          <LogOut className="w-3.5 h-3.5" />
          Déconnexion
        </button>
      </div>
    </aside>
  );
}

function NavSection({ label, items }: { label: string; items: { to: string; label: string; icon: any; exact: boolean }[] }) {
  return (
    <div>
      <p className="px-2 mb-1 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--sidebar-muted)', fontSize: 10 }}>{label}</p>
      <div className="space-y-0.5">
        {items.map(({ to, label, icon: Icon, exact }) => (
          <NavLink key={to} to={to} end={exact}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px',
              borderRadius: 6, fontSize: 13, fontWeight: isActive ? 500 : 400,
              textDecoration: 'none',
              color: isActive ? '#fff' : 'var(--sidebar-text)',
              background: isActive ? 'rgba(37,99,235,0.2)' : 'transparent',
              transition: 'all 0.1s',
            })}
            onMouseEnter={e => { if (!e.currentTarget.getAttribute('aria-current')) e.currentTarget.style.background = 'var(--sidebar-hover)'; }}
            onMouseLeave={e => { if (!e.currentTarget.getAttribute('aria-current')) e.currentTarget.style.background = 'transparent'; }}
          >
            <Icon size={13} />
            {label}
          </NavLink>
        ))}
      </div>
    </div>
  );
}
