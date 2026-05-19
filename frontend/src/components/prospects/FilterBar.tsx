import { useState } from 'react';
import { Filter, X, ChevronDown } from 'lucide-react';
import type { ProspectFilters } from '../../types';

interface FilterBarProps {
  filters: ProspectFilters;
  onChange: (filters: ProspectFilters) => void;
  total?: number;
}

const REGIONS = [
  'Auvergne-Rhône-Alpes', 'Bourgogne-Franche-Comté', 'Bretagne',
  'Centre-Val de Loire', 'Corse', 'Grand Est', 'Hauts-de-France',
  'Île-de-France', 'Normandie', 'Nouvelle-Aquitaine', 'Occitanie',
  'Pays de la Loire', "Provence-Alpes-Côte d'Azur",
];

export function FilterBar({ filters, onChange, total }: FilterBarProps) {
  const [expanded, setExpanded] = useState(true);

  const activeCount = Object.values(filters).filter(v => v !== undefined && v !== '' && v !== null).length;
  const clear = () => onChange({});
  const set = (key: keyof ProspectFilters, value: any) =>
    onChange({ ...filters, [key]: value || undefined });

  const selectStyle: React.CSSProperties = {
    width: '100%', padding: '0.4375rem 0.75rem',
    borderRadius: '8px', border: '1px solid var(--border-color)',
    background: '#fff', color: 'var(--text-primary)',
    fontSize: '0.8125rem', outline: 'none',
    appearance: 'auto' as any,
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '0.4375rem 0.75rem',
    borderRadius: '8px', border: '1px solid var(--border-color)',
    background: '#fff', color: 'var(--text-primary)',
    fontSize: '0.8125rem', outline: 'none', boxSizing: 'border-box' as const,
  };

  const labelStyle: React.CSSProperties = {
    display: 'block', fontSize: '0.7rem', fontWeight: 700,
    color: 'var(--text-muted)', textTransform: 'uppercase',
    letterSpacing: '0.05em', marginBottom: '0.375rem',
  };

  return (
    <div style={{ background: '#fff', border: '1px solid var(--border-color)', borderRadius: '10px', overflow: 'hidden' }}>

      {/* Toggle bar */}
      <button
        onClick={() => setExpanded(v => !v)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0.75rem 1rem', background: 'none', border: 'none', cursor: 'pointer',
          transition: 'background 0.1s',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-tertiary)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'none')}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={14} color="var(--accent-blue)" />
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>Filtres</span>
          {activeCount > 0 && (
            <span style={{
              padding: '1px 7px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 700,
              background: 'var(--accent-blue)', color: '#fff',
            }}>
              {activeCount}
            </span>
          )}
          {total !== undefined && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {total.toLocaleString('fr-FR')} résultat{total > 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          {activeCount > 0 && (
            <button
              onClick={e => { e.stopPropagation(); clear(); }}
              style={{
                display: 'flex', alignItems: 'center', gap: '3px', fontSize: '0.75rem',
                color: 'var(--accent-red)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontWeight: 500,
              }}
            >
              <X size={12} /> Réinitialiser
            </button>
          )}
          <ChevronDown size={15} color="var(--text-muted)"
            style={{ transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
        </div>
      </button>

      {expanded && (
        <div style={{
          borderTop: '1px solid var(--border-color)',
          padding: '1rem',
          display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '0.875rem',
        }}>

          {/* Catégorie */}
          <div>
            <label style={labelStyle}>Catégorie</label>
            <select value={filters.propensity_category || ''} onChange={e => set('propensity_category', e.target.value)} style={selectStyle}>
              <option value="">Toutes</option>
              <option value="HOT">🔥 HOT</option>
              <option value="WARM">🌡 WARM</option>
              <option value="COLD">❄️ COLD</option>
            </select>
          </div>

          {/* Région */}
          <div>
            <label style={labelStyle}>Région</label>
            <select value={filters.region || ''} onChange={e => set('region', e.target.value)} style={selectStyle}>
              <option value="">Toutes</option>
              {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          {/* Département */}
          <div>
            <label style={labelStyle}>Département</label>
            <input
              type="text" value={filters.department || ''}
              onChange={e => set('department', e.target.value)}
              placeholder="Ex: 59" maxLength={3} style={inputStyle}
              onFocus={e => { e.target.style.borderColor = 'var(--accent-blue)'; e.target.style.boxShadow = '0 0 0 3px rgba(52,104,246,0.1)'; }}
              onBlur={e => { e.target.style.borderColor = 'var(--border-color)'; e.target.style.boxShadow = 'none'; }}
            />
          </div>

          {/* Code NAF */}
          <div>
            <label style={labelStyle}>Code NAF</label>
            <input
              type="text" value={filters.naf_code || ''}
              onChange={e => set('naf_code', e.target.value)}
              placeholder="Ex: 62.01" style={inputStyle}
              onFocus={e => { e.target.style.borderColor = 'var(--accent-blue)'; e.target.style.boxShadow = '0 0 0 3px rgba(52,104,246,0.1)'; }}
              onBlur={e => { e.target.style.borderColor = 'var(--border-color)'; e.target.style.boxShadow = 'none'; }}
            />
          </div>

          {/* Site web */}
          <div>
            <label style={labelStyle}>Site web</label>
            <select
              value={filters.has_website === true ? 'true' : filters.has_website === false ? 'false' : ''}
              onChange={e => set('has_website', e.target.value === '' ? undefined : e.target.value === 'true')}
              style={selectStyle}
            >
              <option value="">Tous</option>
              <option value="true">Avec site</option>
              <option value="false">Sans site</option>
            </select>
          </div>

          {/* Téléphone */}
          <div>
            <label style={labelStyle}>Téléphone</label>
            <select
              value={filters.has_phone === true ? 'true' : filters.has_phone === false ? 'false' : ''}
              onChange={e => set('has_phone', e.target.value === '' ? undefined : e.target.value === 'true')}
              style={selectStyle}
            >
              <option value="">Tous</option>
              <option value="true">Avec tél.</option>
              <option value="false">Sans tél.</option>
            </select>
          </div>

          {/* Score min */}
          <div>
            <label style={labelStyle}>Score min</label>
            <input
              type="number" value={filters.min_score ?? ''}
              onChange={e => set('min_score', e.target.value ? Number(e.target.value) : undefined)}
              min={0} max={100} placeholder="0-100" style={inputStyle}
              onFocus={e => { e.target.style.borderColor = 'var(--accent-blue)'; e.target.style.boxShadow = '0 0 0 3px rgba(52,104,246,0.1)'; }}
              onBlur={e => { e.target.style.borderColor = 'var(--border-color)'; e.target.style.boxShadow = 'none'; }}
            />
          </div>

          {/* Tags */}
          <div>
            <label style={labelStyle}>Tags</label>
            <input
              type="text" value={filters.tags || ''}
              onChange={e => set('tags', e.target.value)}
              placeholder="IT, B2B, ..." style={inputStyle}
              onFocus={e => { e.target.style.borderColor = 'var(--accent-blue)'; e.target.style.boxShadow = '0 0 0 3px rgba(52,104,246,0.1)'; }}
              onBlur={e => { e.target.style.borderColor = 'var(--border-color)'; e.target.style.boxShadow = 'none'; }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
