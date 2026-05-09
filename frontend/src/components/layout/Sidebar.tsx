import { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Table2, Workflow, Users, Puzzle, Settings,
  LogOut, Sparkles, Webhook, Mail, Bell, ArrowDownToLine,
  Target, RefreshCw, UserSearch, Zap, ChevronRight,
  Bot, BarChart3, Search, Command
} from 'lucide-react';
import { useAuthStore } from '../../hooks/useAuth';

const NAV = [
  {
    section: 'Principal',
    items: [
      { to: '/',         label: 'Dashboard',    icon: LayoutDashboard, exact: true },
      { to: '/table',    label: 'Spreadsheet',  icon: Table2 },
      { to: '/pipeline', label: 'Pipeline',     icon: Workflow },
      { to: '/prospects',label: 'Prospects',    icon: Users },
    ],
  },
  {
    section: 'Marketing',
    items: [
      { to: '/signals',  label: 'Signals',      icon: Bell,             badge: 'new' },
      { to: '/inbound',  label: 'Inbound',      icon: ArrowDownToLine },
      { to: '/abm',      label: 'ABM & TAM',    icon: Target },
    ],
  },
  {
    section: 'Sales',
    items: [
      { to: '/contacts',   label: 'Contact Intel', icon: UserSearch },
      { to: '/sequences',  label: 'Séquences',     icon: Mail },
      { to: '/crm',        label: 'CRM Sync',      icon: RefreshCw },
    ],
  },
  {
    section: 'Intelligence',
    items: [
      { to: '/agent',    label: 'AI Agent',     icon: Bot },
      { to: '/analytics',label: 'Analytics',   icon: BarChart3 },
      { to: '/webhooks', label: 'Webhooks',     icon: Webhook },
    ],
  },
  {
    section: 'Système',
    items: [
      { to: '/plugins',  label: 'Plugins',      icon: Puzzle },
      { to: '/settings', label: 'Paramètres',   icon: Settings },
    ],
  },
];

interface SidebarProps {
  onOpenCommand?: () => void;
}

export function Sidebar({ onOpenCommand }: SidebarProps) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const appName = import.meta.env.VITE_APP_NAME || 'B2B Prospector';

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
    : 'U';

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">BP</div>
        <div className="sidebar-wordmark">
          <div className="sidebar-appname">{appName}</div>
          <div className="sidebar-tagline">GTM Intelligence</div>
        </div>
      </div>

      {/* Search / Command */}
      <div className="sidebar-search" onClick={onOpenCommand}>
        <Search size={13} style={{ color: 'var(--sidebar-muted)', flexShrink: 0 }} />
        <span className="sidebar-search-text">Rechercher…</span>
        <span className="sidebar-search-kbd">⌘K</span>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {NAV.map(({ section, items }) => (
          <div key={section} className="sidebar-section">
            <div className="sidebar-section-label">{section}</div>
            {items.map(({ to, label, icon: Icon, exact, badge }) => (
              <NavLink
                key={to}
                to={to}
                end={exact}
                className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
              >
                <Icon className="sidebar-link-icon" size={15} />
                <span style={{ flex: 1 }}>{label}</span>
                {badge === 'new' && (
                  <span className="sidebar-link-badge">new</span>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        {user && (
          <div className="sidebar-user" onClick={async () => { await logout(); navigate('/login'); }}>
            <div className="sidebar-avatar">{initials}</div>
            <div className="sidebar-user-info" style={{ flex: 1, minWidth: 0 }}>
              <div className="sidebar-user-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.full_name}
              </div>
              <div className="sidebar-user-role">{user.role}</div>
            </div>
            <LogOut size={13} style={{ color: 'var(--sidebar-muted)', flexShrink: 0 }} />
          </div>
        )}
      </div>
    </aside>
  );
}
