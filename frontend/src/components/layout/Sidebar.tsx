import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Building2, GitBranch, BarChart2,
  Search, Table2, Bell, Mail, Download, Target, RefreshCw,
  Bot, User, Webhook, Puzzle, Settings, ChevronDown,
} from 'lucide-react';

interface NavItem { to: string; icon: React.ReactNode; label: string; badge?: string; }
interface NavSection { label: string; items: NavItem[]; }

const NAV: NavSection[] = [
  {
    label: 'Main Menu',
    items: [
      { to: '/', icon: <LayoutDashboard size={16} />, label: 'Dashboard' },
      { to: '/prospects', icon: <Building2 size={16} />, label: 'Prospects' },
      { to: '/pipeline', icon: <GitBranch size={16} />, label: 'Pipeline' },
      { to: '/analytics', icon: <BarChart2 size={16} />, label: 'Analytics' },
    ],
  },
  {
    label: 'Sourcing',
    items: [
      { to: '/sourcing', icon: <Search size={16} />, label: 'Scraping' },
      { to: '/table', icon: <Table2 size={16} />, label: 'Spreadsheet' },
      { to: '/signals', icon: <Bell size={16} />, label: 'Signaux' },
    ],
  },
  {
    label: 'Marketing & Sales',
    items: [
      { to: '/sequencer', icon: <Mail size={16} />, label: 'Séquences Email' },
      { to: '/inbound', icon: <Download size={16} />, label: 'Inbound' },
      { to: '/abm', icon: <Target size={16} />, label: 'ABM / TAM' },
      { to: '/crm-sync', icon: <RefreshCw size={16} />, label: 'CRM Sync' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { to: '/agent', icon: <Bot size={16} />, label: 'Agent IA' },
      { to: '/contacts', icon: <User size={16} />, label: 'Contacts' },
    ],
  },
  {
    label: 'Système',
    items: [
      { to: '/webhooks', icon: <Webhook size={16} />, label: 'Webhooks' },
      { to: '/plugins', icon: <Puzzle size={16} />, label: 'Plugins' },
      { to: '/settings', icon: <Settings size={16} />, label: 'Paramètres' },
    ],
  },
];

export default function Sidebar() {
  return (
    <aside style={{
      width: 'var(--sidebar-width)', minWidth: 'var(--sidebar-width)',
      height: '100vh', background: '#fff',
      borderRight: '1px solid var(--border-color)',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
      boxShadow: '2px 0 8px rgba(0,0,0,.04)',
    }}>

      {/* Logo */}
      <div style={{
        height: 'var(--header-height)',
        display: 'flex', alignItems: 'center',
        padding: '0 1.25rem',
        borderBottom: '1px solid var(--border-color)',
        flexShrink: 0, gap: '.75rem',
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: 8,
          background: 'var(--grad-blue)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontWeight: 800, fontSize: '1.125rem',
          boxShadow: '0 4px 10px rgba(13,110,253,.3)',
        }}>B</div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '.9375rem', color: 'var(--text-primary)', lineHeight: 1.2 }}>
            B2B Prospector
          </div>
          <div style={{ fontSize: '.6875rem', color: 'var(--text-muted)' }}>CRM & Sourcing</div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '.5rem .625rem' }}>
        {NAV.map(section => (
          <div key={section.label} style={{ marginBottom: '.25rem' }}>
            <div style={{
              fontSize: '.6875rem', fontWeight: 700,
              color: 'var(--text-muted)', textTransform: 'uppercase',
              letterSpacing: '.08em', padding: '.625rem .5rem .3125rem',
            }}>
              {section.label}
            </div>
            {section.items.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                style={({ isActive }) => ({
                  display: 'flex', alignItems: 'center', gap: '.625rem',
                  padding: '.5625rem .875rem', borderRadius: 6,
                  color: isActive ? '#0d6efd' : 'var(--text-secondary)',
                  background: isActive ? 'rgba(13,110,253,.1)' : 'transparent',
                  fontWeight: isActive ? 600 : 400,
                  fontSize: '.875rem', textDecoration: 'none',
                  transition: 'all .15s', marginBottom: 2,
                  borderLeft: isActive ? '3px solid #0d6efd' : '3px solid transparent',
                })}
                onMouseEnter={e => {
                  const el = e.currentTarget as HTMLElement;
                  if (!el.style.background.includes('0.1')) {
                    el.style.background = 'var(--bg-hover)';
                    el.style.color = '#0d6efd';
                  }
                }}
                onMouseLeave={e => {
                  const el = e.currentTarget as HTMLElement;
                  if (!el.style.background.includes('0.1')) {
                    el.style.background = 'transparent';
                    el.style.color = 'var(--text-secondary)';
                  }
                }}
              >
                <span style={{ color: 'inherit', display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                  {item.icon}
                </span>
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.badge && (
                  <span style={{
                    padding: '1px 7px', borderRadius: 20, fontSize: '.7rem',
                    fontWeight: 700, background: '#0d6efd', color: '#fff',
                  }}>{item.badge}</span>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* User footer */}
      <div style={{
        padding: '.875rem 1rem', borderTop: '1px solid var(--border-color)', flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: '.625rem',
      }}>
        <div style={{
          width: 34, height: 34, borderRadius: 8,
          background: 'var(--grad-purple)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontWeight: 700, fontSize: '.8125rem', flexShrink: 0,
        }}>AD</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '.8125rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            Admin
          </div>
          <div style={{ fontSize: '.7rem', color: 'var(--text-muted)' }}>Administrateur</div>
        </div>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#198754', flexShrink: 0, boxShadow: '0 0 0 2px rgba(25,135,84,.2)' }} />
      </div>
    </aside>
  );
}
