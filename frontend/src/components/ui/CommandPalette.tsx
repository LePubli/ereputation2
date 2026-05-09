import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ArrowRight, LayoutDashboard, Table2, Workflow, Users, Bot, Bell, Mail, Target, UserSearch, Webhook, Settings, Plus, Download } from 'lucide-react';

const COMMANDS = [
  {
    section: 'Navigation',
    items: [
      { id: 'nav-dash',      label: 'Dashboard',          icon: LayoutDashboard, shortcut: 'G D', action: 'nav', to: '/' },
      { id: 'nav-table',     label: 'Spreadsheet',         icon: Table2,          shortcut: 'G T', action: 'nav', to: '/table' },
      { id: 'nav-pipeline',  label: 'Pipeline Kanban',     icon: Workflow,        shortcut: 'G P', action: 'nav', to: '/pipeline' },
      { id: 'nav-prospects', label: 'Prospects',           icon: Users,           shortcut: 'G R', action: 'nav', to: '/prospects' },
      { id: 'nav-signals',   label: 'Signals & Intent',    icon: Bell,            action: 'nav', to: '/signals' },
      { id: 'nav-contacts',  label: 'Contact Intelligence',icon: UserSearch,      action: 'nav', to: '/contacts' },
      { id: 'nav-sequences', label: 'Séquences email',     icon: Mail,            action: 'nav', to: '/sequences' },
      { id: 'nav-abm',       label: 'ABM & TAM Sourcing',  icon: Target,          action: 'nav', to: '/abm' },
      { id: 'nav-agent',     label: 'AI Agent',            icon: Bot,             shortcut: 'G A', action: 'nav', to: '/agent' },
      { id: 'nav-webhooks',  label: 'Webhooks',            icon: Webhook,         action: 'nav', to: '/webhooks' },
      { id: 'nav-settings',  label: 'Paramètres',          icon: Settings,        action: 'nav', to: '/settings' },
    ],
  },
  {
    section: 'Actions rapides',
    items: [
      { id: 'act-new-prospect',  label: 'Nouveau prospect (SIRET)',  icon: Plus,     shortcut: 'N', action: 'emit', event: 'open-add-prospect' },
      { id: 'act-import',        label: 'Importer CSV',              icon: Plus,     action: 'emit', event: 'open-import' },
      { id: 'act-export',        label: 'Exporter CSV',              icon: Download, action: 'emit', event: 'export-csv' },
    ],
  },
];

interface CommandPaletteProps {
  onClose: () => void;
}

export function CommandPalette({ onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => { inputRef.current?.focus(); }, []);

  const allItems = COMMANDS.flatMap(s => s.items);

  const filtered = query
    ? allItems.filter(i => i.label.toLowerCase().includes(query.toLowerCase()))
    : allItems;

  const grouped = query
    ? [{ section: 'Résultats', items: filtered }]
    : COMMANDS.map(s => ({ ...s, items: s.items.filter(i => filtered.includes(i)) })).filter(s => s.items.length > 0);

  const flatFiltered = grouped.flatMap(g => g.items);

  useEffect(() => { setActiveIdx(0); }, [query]);

  const execute = (item: typeof allItems[0]) => {
    if (item.action === 'nav' && item.to) {
      navigate(item.to);
    } else if (item.action === 'emit' && item.event) {
      window.dispatchEvent(new CustomEvent(item.event));
    }
    onClose();
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, flatFiltered.length - 1)); }
    if (e.key === 'ArrowUp')   { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && flatFiltered[activeIdx]) execute(flatFiltered[activeIdx]);
    if (e.key === 'Escape') onClose();
  };

  return (
    <div className="cmd-overlay" onClick={onClose}>
      <div className="cmd-box" onClick={e => e.stopPropagation()} onKeyDown={handleKey}>
        {/* Input */}
        <div className="cmd-input-wrap">
          <Search size={16} style={{ color: 'var(--tx-muted)', flexShrink: 0 }} />
          <input
            ref={inputRef}
            className="cmd-input"
            placeholder="Rechercher une page, une action…"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          {query && (
            <button onClick={() => setQuery('')} style={{ color: 'var(--tx-muted)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 12 }}>
              Effacer
            </button>
          )}
        </div>

        {/* Results */}
        <div className="cmd-results">
          {flatFiltered.length === 0 && (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--tx-muted)', fontSize: 13 }}>
              Aucun résultat pour « {query} »
            </div>
          )}
          {grouped.map(group => (
            <div key={group.section}>
              <div className="cmd-section-label">{group.section}</div>
              {group.items.map(item => {
                const Icon = item.icon;
                const isActive = flatFiltered.indexOf(item) === activeIdx;
                return (
                  <div
                    key={item.id}
                    className={`cmd-item ${isActive ? 'active' : ''}`}
                    onClick={() => execute(item)}
                    onMouseEnter={() => setActiveIdx(flatFiltered.indexOf(item))}
                  >
                    <div className="cmd-item-icon">
                      <Icon size={14} style={{ color: 'var(--tx-secondary)' }} />
                    </div>
                    <span className="cmd-item-label">{item.label}</span>
                    {item.shortcut && (
                      <div style={{ display: 'flex', gap: 4 }}>
                        {item.shortcut.split(' ').map((k, i) => (
                          <span key={i} className="cmd-kbd">{k}</span>
                        ))}
                      </div>
                    )}
                    <ArrowRight size={12} style={{ color: 'var(--tx-muted)', opacity: isActive ? 1 : 0 }} />
                  </div>
                );
              })}
            </div>
          ))}
        </div>

        {/* Footer hints */}
        <div className="cmd-footer">
          <div className="cmd-hint"><span className="cmd-kbd">↑↓</span> Naviguer</div>
          <div className="cmd-hint"><span className="cmd-kbd">↵</span> Ouvrir</div>
          <div className="cmd-hint"><span className="cmd-kbd">Esc</span> Fermer</div>
        </div>
      </div>
    </div>
  );
}
