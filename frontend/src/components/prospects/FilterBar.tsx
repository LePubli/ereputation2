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
  'Centre-Val de Loire', 'Corse', 'Grand Est', 'Guadeloupe',
  'Guyane', 'Hauts-de-France', 'Île-de-France', 'La Réunion',
  'Martinique', 'Mayotte', 'Normandie', 'Nouvelle-Aquitaine',
  'Occitanie', 'Pays de la Loire', "Provence-Alpes-Côte d'Azur",
];

export function FilterBar({ filters, onChange, total }: FilterBarProps) {
  const [expanded, setExpanded] = useState(false);

  const activeCount = Object.values(filters).filter(
    (v) => v !== undefined && v !== '' && v !== null
  ).length;

  const clear = () => onChange({});

  const set = (key: keyof ProspectFilters, value: any) =>
    onChange({ ...filters, [key]: value || undefined });

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Toggle bar */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 transition"
      >
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium">Filtres</span>
          {activeCount > 0 && (
            <span className="px-1.5 py-0.5 bg-blue-600 text-white text-xs rounded-full">{activeCount}</span>
          )}
          {total !== undefined && (
            <span className="text-xs text-gray-500">{total} résultat(s)</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {activeCount > 0 && (
            <button
              onClick={(e) => { e.stopPropagation(); clear(); }}
              className="text-xs text-red-500 hover:text-red-700 flex items-center gap-0.5"
            >
              <X className="w-3.5 h-3.5" /> Réinitialiser
            </button>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition ${expanded ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {expanded && (
        <div className="border-t px-4 py-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {/* Score */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Catégorie</label>
            <select
              value={filters.propensity_category || ''}
              onChange={(e) => set('propensity_category', e.target.value)}
              className="w-full text-sm px-2 py-1.5 border rounded"
            >
              <option value="">Toutes</option>
              <option value="HOT">🔥 HOT</option>
              <option value="WARM">🌡 WARM</option>
              <option value="COLD">❄️ COLD</option>
            </select>
          </div>

          {/* Région */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Région</label>
            <select
              value={filters.region || ''}
              onChange={(e) => set('region', e.target.value)}
              className="w-full text-sm px-2 py-1.5 border rounded"
            >
              <option value="">Toutes</option>
              {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          {/* Département */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Département</label>
            <input
              type="text"
              value={filters.department || ''}
              onChange={(e) => set('department', e.target.value)}
              placeholder="Ex: 59"
              maxLength={3}
              className="w-full text-sm px-2 py-1.5 border rounded"
            />
          </div>

          {/* Code NAF */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Code NAF</label>
            <input
              type="text"
              value={filters.naf_code || ''}
              onChange={(e) => set('naf_code', e.target.value)}
              placeholder="Ex: 62.01"
              className="w-full text-sm px-2 py-1.5 border rounded"
            />
          </div>

          {/* Source */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Source</label>
            <select
              value={filters.source || ''}
              onChange={(e) => set('source', e.target.value)}
              className="w-full text-sm px-2 py-1.5 border rounded"
            >
              <option value="">Toutes</option>
              <option value="siret">SIREN/SIRET</option>
              <option value="import">Import CSV</option>
              <option value="manual">Manuel</option>
              <option value="seed">Démo</option>
            </select>
          </div>

          {/* Site web */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Site web</label>
            <select
              value={filters.has_website === true ? 'true' : filters.has_website === false ? 'false' : ''}
              onChange={(e) => set('has_website', e.target.value === '' ? undefined : e.target.value === 'true')}
              className="w-full text-sm px-2 py-1.5 border rounded"
            >
              <option value="">Tous</option>
              <option value="true">Avec site</option>
              <option value="false">Sans site</option>
            </select>
          </div>

          {/* Score min */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Score min</label>
            <input
              type="number"
              value={filters.min_score ?? ''}
              onChange={(e) => set('min_score', e.target.value ? Number(e.target.value) : undefined)}
              min={0} max={100}
              placeholder="0-100"
              className="w-full text-sm px-2 py-1.5 border rounded"
            />
          </div>

          {/* Tri */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Trier par</label>
            <div className="flex gap-1">
              <select
                value={filters.sort_by || 'created_at'}
                onChange={(e) => set('sort_by', e.target.value)}
                className="flex-1 text-sm px-2 py-1.5 border rounded"
              >
                <option value="created_at">Date</option>
                <option value="company_name">Nom</option>
                <option value="propensity_score">Score</option>
                <option value="estimated_revenue">CA</option>
                <option value="last_activity_at">Dernière activité</option>
              </select>
              <button
                onClick={() => set('sort_dir', filters.sort_dir === 'asc' ? 'desc' : 'asc')}
                className="px-2 py-1.5 border rounded text-sm"
                title={filters.sort_dir === 'asc' ? 'Croissant' : 'Décroissant'}
              >
                {filters.sort_dir === 'asc' ? '↑' : '↓'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
