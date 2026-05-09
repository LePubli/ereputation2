import { useState, useEffect, useCallback, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { CommandPalette } from '../ui/CommandPalette';

export function AppShell({ children }: { children: ReactNode }) {
  const [cmdOpen, setCmdOpen] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCmdOpen(v => !v);
      }
      if (e.key === 'Escape') setCmdOpen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return (
    <div className="app">
      <Sidebar onOpenCommand={() => setCmdOpen(true)} />
      <main className="app-main">
        {children}
      </main>
      {cmdOpen && <CommandPalette onClose={() => setCmdOpen(false)} />}
    </div>
  );
}

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  count?: number;
  tabs?: { id: string; label: string; count?: number }[];
  activeTab?: string;
  onTabChange?: (id: string) => void;
}

export function PageHeader({ title, description, actions, count, tabs, activeTab, onTabChange }: PageHeaderProps) {
  return (
    <div style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-header-title">{title}</h1>
          {count !== undefined && (
            <span style={{
              fontSize: 11, fontWeight: 600, color: 'var(--tx-muted)',
              background: 'var(--bg-subtle)', border: '1px solid var(--border)',
              padding: '2px 8px', borderRadius: 99
            }}>{count.toLocaleString('fr-FR')}</span>
          )}
          {description && <span className="page-header-sub" style={{ display: 'none' }}>{description}</span>}
        </div>
        {actions && <div className="page-header-right">{actions}</div>}
      </div>
      {tabs && (
        <div className="tabs" style={{ padding: '0 24px' }}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => onTabChange?.(tab.id)}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span style={{
                  marginLeft: 6, fontSize: 10, fontWeight: 600,
                  background: activeTab === tab.id ? 'var(--brand-100)' : 'var(--bg-subtle)',
                  color: activeTab === tab.id ? 'var(--brand-700)' : 'var(--tx-muted)',
                  padding: '1px 6px', borderRadius: 99
                }}>{tab.count}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
