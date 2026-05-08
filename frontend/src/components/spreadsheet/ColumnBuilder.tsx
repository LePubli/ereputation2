import { useState } from 'react';
import { X, GripVertical, Eye, EyeOff, Plus, Sparkles } from 'lucide-react';
import type { ColumnConfig } from '../../types';

const SOURCES = [
  { id: 'core', label: 'B2B Prospector', color: '#6b7280' },
  { id: 'insee', label: 'INSEE / Sirene', color: '#2563eb' },
  { id: 'bodacc', label: 'BODACC', color: '#be185d' },
  { id: 'pappers', label: 'Pappers', color: '#16a34a' },
  { id: 'pages_jaunes', label: 'Pages Jaunes', color: '#d97706' },
  { id: 'google_maps', label: 'Google Maps', color: '#ea580c' },
  { id: 'societe_com', label: 'Société.com', color: '#dc2626' },
  { id: 'trustpilot', label: 'Trustpilot', color: '#065f46' },
  { id: 'ai_agent', label: '✨ AI Agent', color: '#7c3aed' },
];

const DISPLAY_TYPES = [
  { id: 'text', label: 'Texte' },
  { id: 'mono', label: 'Code / SIREN' },
  { id: 'phone', label: 'Téléphone' },
  { id: 'url', label: 'URL / Site web' },
  { id: 'email', label: 'Email' },
  { id: 'score', label: 'Score (barre)' },
  { id: 'category', label: 'Catégorie (badge)' },
  { id: 'badge', label: 'Badge texte' },
  { id: 'boolean', label: 'Oui / Non' },
  { id: 'sources', label: 'Sources utilisées' },
  { id: 'ai', label: '✨ Colonne IA' },
];

const FIELD_SUGGESTIONS: Record<string, { path: string; label: string; type: string }[]> = {
  core: [
    { path: 'company_name', label: 'Nom entreprise', type: 'text' },
    { path: 'siren', label: 'SIREN', type: 'mono' },
    { path: 'city', label: 'Ville', type: 'text' },
    { path: 'phone', label: 'Téléphone', type: 'phone' },
    { path: 'email', label: 'Email', type: 'email' },
    { path: 'website', label: 'Site web', type: 'url' },
    { path: 'propensity_score', label: 'Score', type: 'score' },
    { path: 'propensity_category', label: 'Catégorie', type: 'category' },
  ],
  insee: [
    { path: 'naf_code', label: 'Code NAF', type: 'mono' },
    { path: 'naf_label', label: 'Secteur d\'activité', type: 'text' },
    { path: 'employee_range', label: 'Effectifs', type: 'badge' },
    { path: 'legal_form', label: 'Forme juridique', type: 'badge' },
    { path: 'creation_date', label: 'Date création', type: 'text' },
  ],
  bodacc: [
    { path: 'enrichment.bodacc_signals.has_collective_procedure', label: 'Procédure collective', type: 'boolean' },
    { path: 'enrichment.bodacc_signals.annonces_count', label: 'Nbre annonces', type: 'text' },
  ],
  google_maps: [
    { path: 'enrichment.rating', label: 'Note Google', type: 'score' },
    { path: 'enrichment.reviews_count', label: 'Nbre avis', type: 'text' },
  ],
  ai_agent: [
    { path: 'ca_estime', label: 'CA estimé (IA)', type: 'ai' },
    { path: 'positionnement', label: 'Positionnement (IA)', type: 'ai' },
    { path: 'signaux_croissance', label: 'Signaux croissance (IA)', type: 'ai' },
    { path: 'decideur', label: 'Décideur (IA)', type: 'ai' },
  ],
};

interface ColumnBuilderProps {
  columns: ColumnConfig[];
  onSave: (columns: ColumnConfig[]) => void;
  onClose: () => void;
}

export function ColumnBuilder({ columns, onSave, onClose }: ColumnBuilderProps) {
  const [cols, setCols] = useState<ColumnConfig[]>(columns);
  const [newCol, setNewCol] = useState({
    source: 'core',
    name: '',
    field_path: '',
    display_type: 'text',
    width: 180,
  });

  const addColumn = () => {
    if (!newCol.name || !newCol.field_path) return;
    const col: ColumnConfig = {
      id: `col_${Date.now()}`,
      ...newCol,
      is_visible: true,
    };
    setCols([...cols, col]);
    setNewCol({ source: 'core', name: '', field_path: '', display_type: 'text', width: 180 });
  };

  const addSuggestion = (s: { path: string; label: string; type: string }, source: string) => {
    const existing = cols.find((c) => c.field_path === s.path);
    if (existing) return;
    setCols([...cols, {
      id: `col_${Date.now()}`,
      name: s.label,
      source,
      field_path: s.path,
      display_type: s.type,
      width: 180,
      is_visible: true,
    }]);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex overflow-hidden">
        {/* Sidebar sources */}
        <div className="w-64 border-r bg-gray-50 flex flex-col flex-shrink-0">
          <div className="px-4 py-4 border-b">
            <h3 className="font-semibold text-sm">Sources disponibles</h3>
            <p className="text-xs text-gray-500 mt-0.5">Cliquez pour voir les champs</p>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {SOURCES.map((src) => {
              const suggestions = FIELD_SUGGESTIONS[src.id] || [];
              return (
                <div key={src.id} className="mb-3">
                  <div className="flex items-center gap-1.5 px-2 py-1">
                    <span className="w-2 h-2 rounded-full" style={{ background: src.color }} />
                    <span className="text-xs font-medium text-gray-700">{src.label}</span>
                  </div>
                  {suggestions.map((s) => {
                    const already = cols.some((c) => c.field_path === s.path);
                    return (
                      <button
                        key={s.path}
                        onClick={() => addSuggestion(s, src.id)}
                        disabled={already}
                        className={`w-full text-left px-3 py-1 text-xs rounded hover:bg-blue-50 hover:text-blue-700 transition
                          ${already ? 'text-gray-300 cursor-not-allowed' : 'text-gray-600'}`}
                      >
                        {already ? '✓ ' : '+ '}{s.label}
                      </button>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="font-bold text-lg">Gérer les colonnes</h2>
            <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Colonnes actives */}
          <div className="flex-1 overflow-y-auto p-4 space-y-1">
            <p className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">
              Colonnes actives ({cols.filter(c => c.is_visible).length}/{cols.length})
            </p>
            {cols.map((col, idx) => (
              <div key={col.id}
                className="flex items-center gap-2 px-3 py-2 bg-white border rounded hover:border-blue-200 group">
                <GripVertical className="w-4 h-4 text-gray-300 flex-shrink-0" />
                <span className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ background: SOURCES.find(s => s.id === col.source)?.color || '#9ca3af' }} />
                <span className="text-sm font-medium flex-1 truncate">{col.name}</span>
                <span className="text-xs text-gray-400 font-mono truncate max-w-32">{col.field_path}</span>
                <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">{col.display_type}</span>
                <button
                  onClick={() => setCols(cols.map((c, i) => i === idx ? { ...c, is_visible: !c.is_visible } : c))}
                  className="text-gray-400 hover:text-gray-700">
                  {col.is_visible ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => setCols(cols.filter((_, i) => i !== idx))}
                  className="text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}

            {/* Ajouter colonne custom */}
            <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-dashed">
              <p className="text-xs font-medium text-gray-600 mb-2">Colonne personnalisée</p>
              <div className="grid grid-cols-2 gap-2 mb-2">
                <input value={newCol.name} onChange={(e) => setNewCol({ ...newCol, name: e.target.value })}
                  placeholder="Nom de la colonne" className="px-2 py-1.5 text-sm border rounded" />
                <input value={newCol.field_path} onChange={(e) => setNewCol({ ...newCol, field_path: e.target.value })}
                  placeholder="field.path" className="px-2 py-1.5 text-sm border rounded font-mono" />
                <select value={newCol.source} onChange={(e) => setNewCol({ ...newCol, source: e.target.value })}
                  className="px-2 py-1.5 text-sm border rounded">
                  {SOURCES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                </select>
                <select value={newCol.display_type} onChange={(e) => setNewCol({ ...newCol, display_type: e.target.value })}
                  className="px-2 py-1.5 text-sm border rounded">
                  {DISPLAY_TYPES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
                </select>
              </div>
              <button onClick={addColumn}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                <Plus className="w-4 h-4" /> Ajouter
              </button>
            </div>
          </div>

          <div className="flex justify-end gap-2 px-6 py-4 border-t">
            <button onClick={onClose} className="px-4 py-2 border rounded hover:bg-gray-50">Annuler</button>
            <button onClick={() => onSave(cols)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              Appliquer ({cols.filter(c => c.is_visible).length} colonnes)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
