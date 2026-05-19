import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';
import { Palette, Check, Download, Upload, Trash2, Plus, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

interface Theme {
  id: string;
  name: string;
  slug: string;
  description: string;
  author: string;
  version: string;
  preview_color: string;
  preview_bg: string;
  is_active: boolean;
  is_builtin: boolean;
  variables_count: number;
}

export default function ThemesPage() {
  const [themes, setThemes] = useState<Theme[]>([]);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const importRef = useRef<HTMLInputElement>(null);

  useEffect(() => { load(); }, []);

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/themes');
      setThemes(Array.isArray(data) ? data : []);
    } catch { toast.error('Erreur chargement thèmes'); }
    finally { setLoading(false); }
  };

  const activate = async (theme: Theme) => {
    if (theme.is_active) return;
    setActivating(theme.id);
    try {
      const result = await apiClient.post(`/themes/${theme.id}/activate`, {});
      setThemes(prev => prev.map(t => ({ ...t, is_active: t.id === theme.id })));
      // Applique immédiatement via ThemeProvider
      if ((window as any).__refreshTheme) {
        await (window as any).__refreshTheme();
      }
      toast.success(`✨ Thème "${theme.name}" activé`);
    } catch { toast.error('Erreur activation'); }
    finally { setActivating(null); }
  };

  const exportTheme = async (theme: Theme) => {
    try {
      const response = await fetch(`/api/v1/themes/${theme.id}/export`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${theme.slug}.theme.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Thème exporté');
    } catch { toast.error('Erreur export'); }
  };

  const importTheme = async (file: File) => {
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      const result = await apiClient.post('/themes/import', data);
      toast.success(`Thème "${result.name}" importé`);
      load();
    } catch (e) {
      toast.error('Fichier invalide — doit être un .theme.json');
    }
  };

  const deleteTheme = async (theme: Theme) => {
    if (!confirm(`Supprimer le thème "${theme.name}" ?`)) return;
    try {
      await apiClient.delete(`/themes/${theme.id}`);
      setThemes(prev => prev.filter(t => t.id !== theme.id));
      toast.success('Thème supprimé');
    } catch (e: any) {
      toast.error(e?.detail || 'Erreur suppression');
    }
  };

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '1.5rem', background: 'var(--bg-primary)' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            Thèmes
          </h1>
          <p style={{ margin: '3px 0 0', fontSize: '.8125rem', color: 'var(--text-muted)' }}>
            Personnalisez l'apparence de votre application — changement instantané
          </p>
        </div>
        <div style={{ display: 'flex', gap: '.625rem' }}>
          <input ref={importRef} type="file" accept=".json" style={{ display: 'none' }}
            onChange={e => e.target.files?.[0] && importTheme(e.target.files[0])} />
          <button onClick={() => importRef.current?.click()}
            style={{ display: 'flex', alignItems: 'center', gap: '.375rem', padding: '.4375rem .875rem', borderRadius: 8, background: '#fff', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '.8125rem' }}>
            <Upload size={13} /> Importer
          </button>
          <button onClick={() => setShowCreate(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '.375rem', padding: '.4375rem .875rem', borderRadius: 8, background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '.8125rem', fontWeight: 500 }}>
            <Plus size={13} /> Créer un thème
          </button>
        </div>
      </div>

      {/* Thème actif */}
      {themes.find(t => t.is_active) && (
        <div style={{ background: 'rgba(13,110,253,.06)', border: '1px solid rgba(13,110,253,.2)', borderRadius: 10, padding: '1rem 1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '.875rem' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: themes.find(t => t.is_active)!.preview_color, flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
              Thème actif : {themes.find(t => t.is_active)!.name}
            </div>
            <div style={{ fontSize: '.8125rem', color: 'var(--text-muted)' }}>
              {themes.find(t => t.is_active)!.description}
            </div>
          </div>
          <div style={{ marginLeft: 'auto', padding: '3px 10px', borderRadius: 20, fontSize: '.75rem', fontWeight: 700, background: '#198754', color: '#fff' }}>
            ✓ Actif
          </div>
        </div>
      )}

      {/* Grid thèmes */}
      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} style={{ height: 200, borderRadius: 12, background: 'linear-gradient(90deg,#eef2ff 25%,#e5eaf8 50%,#eef2ff 75%)', backgroundSize: '200%', animation: 'shimmer 1.5s infinite' }} />
          ))}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
          {themes.map(theme => (
            <ThemeCard
              key={theme.id}
              theme={theme}
              onActivate={activate}
              onExport={exportTheme}
              onDelete={deleteTheme}
              isActivating={activating === theme.id}
            />
          ))}
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <CreateThemeModal
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load(); }}
        />
      )}

      <style>{`@keyframes shimmer { 0%{background-position:-200% center} 100%{background-position:200% center} }`}</style>
    </div>
  );
}

function ThemeCard({ theme, onActivate, onExport, onDelete, isActivating }: {
  theme: Theme;
  onActivate: (t: Theme) => void;
  onExport: (t: Theme) => void;
  onDelete: (t: Theme) => void;
  isActivating: boolean;
}) {
  return (
    <div style={{
      background: '#fff', border: `2px solid ${theme.is_active ? 'var(--accent-blue)' : 'var(--border-color)'}`,
      borderRadius: 12, overflow: 'hidden', transition: 'all .15s',
      boxShadow: theme.is_active ? '0 0 0 4px rgba(13,110,253,.1)' : 'var(--shadow-card)',
    }}>
      {/* Preview */}
      <div style={{ height: 100, background: theme.preview_bg, position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {/* Mini sidebar preview */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 40, height: 70, borderRadius: 6, background: theme.is_active ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.7)', display: 'flex', flexDirection: 'column', gap: 4, padding: '6px 4px' }}>
            {[0,1,2,3].map(i => <div key={i} style={{ height: 6, borderRadius: 3, background: i === 0 ? theme.preview_color : 'rgba(0,0,0,.1)', width: i === 0 ? '100%' : '70%' }} />)}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {[0,1].map(i => <div key={i} style={{ width: 80, height: 28, borderRadius: 6, background: 'rgba(255,255,255,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ width: 40, height: 6, borderRadius: 3, background: i === 0 ? theme.preview_color : 'rgba(0,0,0,.1)' }} />
            </div>)}
          </div>
        </div>
        {theme.is_active && (
          <div style={{ position: 'absolute', top: 8, right: 8, background: 'var(--accent-blue)', color: '#fff', borderRadius: 20, padding: '2px 8px', fontSize: '.7rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 3 }}>
            <Check size={10} /> Actif
          </div>
        )}
        {theme.is_builtin && (
          <div style={{ position: 'absolute', top: 8, left: 8, background: 'rgba(0,0,0,.5)', color: '#fff', borderRadius: 20, padding: '2px 8px', fontSize: '.7rem', fontWeight: 600 }}>
            Builtin
          </div>
        )}
        <div style={{ position: 'absolute', bottom: 8, right: 8, width: 24, height: 24, borderRadius: '50%', background: theme.preview_color, border: '3px solid #fff', boxShadow: '0 1px 4px rgba(0,0,0,.2)' }} />
      </div>

      {/* Info */}
      <div style={{ padding: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '.5rem' }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '.9375rem', color: 'var(--text-primary)' }}>{theme.name}</div>
            <div style={{ fontSize: '.75rem', color: 'var(--text-muted)' }}>{theme.author} · v{theme.version}</div>
          </div>
        </div>
        {theme.description && (
          <p style={{ margin: '0 0 .875rem', fontSize: '.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
            {theme.description}
          </p>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: '.5rem' }}>
          {!theme.is_active && (
            <button onClick={() => onActivate(theme)} disabled={isActivating}
              style={{ flex: 1, padding: '.5rem', borderRadius: 8, background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontWeight: 600, fontSize: '.8125rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '.375rem' }}>
              {isActivating ? <RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Palette size={12} />}
              Activer
            </button>
          )}
          {theme.is_active && (
            <div style={{ flex: 1, padding: '.5rem', borderRadius: 8, background: 'rgba(25,135,84,.1)', border: '1px solid rgba(25,135,84,.2)', color: '#198754', fontSize: '.8125rem', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '.375rem' }}>
              <Check size={12} /> Thème actif
            </div>
          )}
          <button onClick={() => onExport(theme)}
            style={{ width: 36, height: 36, borderRadius: 8, background: '#f0f4ff', border: '1px solid var(--border-color)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}
            title="Exporter">
            <Download size={14} />
          </button>
          {!theme.is_builtin && !theme.is_active && (
            <button onClick={() => onDelete(theme)}
              style={{ width: 36, height: 36, borderRadius: 8, background: 'rgba(220,53,69,.06)', border: '1px solid rgba(220,53,69,.2)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#dc3545' }}
              title="Supprimer">
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function CreateThemeModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const activeTheme = { slug: 'crmi-light' };
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [desc, setDesc] = useState('');
  const [baseTheme, setBaseTheme] = useState('crmi-light');
  const [accentColor, setAccentColor] = useState('#0d6efd');
  const [bgColor, setBgColor] = useState('#f2f6ff');
  const [creating, setCreating] = useState(false);

  const handleCreate = async () => {
    if (!name || !slug) return;
    setCreating(true);
    try {
      await apiClient.post('/themes', {
        name, slug, description: desc,
        author: 'Custom',
        preview_color: accentColor,
        preview_bg: bgColor,
        css_variables: {
          '--bg-primary': bgColor,
          '--bg-secondary': '#ffffff',
          '--bg-card': '#ffffff',
          '--bg-tertiary': `${accentColor}15`,
          '--bg-sidebar': '#ffffff',
          '--bg-hover': `${accentColor}10`,
          '--border-color': '#e5e9f2',
          '--text-primary': '#212529',
          '--text-secondary': '#6c757d',
          '--text-muted': '#adb5bd',
          '--accent-blue': accentColor,
          '--accent-green': '#198754',
          '--accent-red': '#dc3545',
          '--accent-orange': '#fd7e14',
          '--accent-purple': '#6f42c1',
          '--shadow-card': '0 1px 4px rgba(0,0,0,.08)',
          '--radius-lg': '10px',
        },
      });
      toast.success(`Thème "${name}" créé`);
      onCreated();
    } catch (e: any) {
      toast.error(e?.detail || 'Erreur création');
    } finally { setCreating(false); }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,.5)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ background: '#fff', border: '1px solid var(--border-color)', borderRadius: 14, padding: '1.5rem', width: 480, maxWidth: '95vw', boxShadow: 'var(--shadow-xl)', animation: 'popIn .15s ease' }}>
        <h2 style={{ margin: '0 0 1.25rem', fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          <Palette size={16} style={{ verticalAlign: 'middle', marginRight: '.5rem' }} />
          Créer un thème personnalisé
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '.875rem' }}>
          <Field label="Nom du thème *">
            <input value={name} onChange={e => { setName(e.target.value); setSlug(e.target.value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')); }}
              placeholder="Mon Thème Custom" style={inputStyle} />
          </Field>

          <Field label="Slug *">
            <input value={slug} onChange={e => setSlug(e.target.value)} placeholder="mon-theme-custom" style={inputStyle} />
          </Field>

          <Field label="Description">
            <input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Description optionnelle" style={inputStyle} />
          </Field>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.75rem' }}>
            <Field label="Couleur accent">
              <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
                <input type="color" value={accentColor} onChange={e => setAccentColor(e.target.value)}
                  style={{ width: 40, height: 36, borderRadius: 6, border: '1px solid var(--border-color)', cursor: 'pointer', padding: 2 }} />
                <input value={accentColor} onChange={e => setAccentColor(e.target.value)} style={{ ...inputStyle, flex: 1 }} />
              </div>
            </Field>
            <Field label="Couleur fond">
              <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
                <input type="color" value={bgColor} onChange={e => setBgColor(e.target.value)}
                  style={{ width: 40, height: 36, borderRadius: 6, border: '1px solid var(--border-color)', cursor: 'pointer', padding: 2 }} />
                <input value={bgColor} onChange={e => setBgColor(e.target.value)} style={{ ...inputStyle, flex: 1 }} />
              </div>
            </Field>
          </div>

          {/* Preview */}
          <div style={{ height: 60, borderRadius: 8, background: bgColor, border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
            <div style={{ width: 30, height: 44, borderRadius: 4, background: 'rgba(255,255,255,.9)' }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div style={{ width: 80, height: 18, borderRadius: 4, background: accentColor, opacity: .9 }} />
              <div style={{ width: 80, height: 14, borderRadius: 4, background: 'rgba(255,255,255,.7)' }} />
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '.5rem', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
          <button onClick={onClose} style={{ padding: '.5rem 1rem', borderRadius: 8, background: '#f0f4ff', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '.875rem' }}>
            Annuler
          </button>
          <button onClick={handleCreate} disabled={creating || !name || !slug}
            style={{ padding: '.5rem 1.25rem', borderRadius: 8, background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontWeight: 600, fontSize: '.875rem', opacity: (creating || !name || !slug) ? .6 : 1 }}>
            {creating ? 'Création...' : 'Créer le thème'}
          </button>
        </div>
      </div>
      <style>{`@keyframes popIn { from{opacity:0;transform:scale(.96)} to{opacity:1;transform:scale(1)} }`}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '.375rem' }}>{label}</label>
      {children}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '.5rem .75rem', borderRadius: 8,
  border: '1px solid var(--border-color)', background: '#fff',
  color: 'var(--text-primary)', fontSize: '.875rem',
  outline: 'none', boxSizing: 'border-box',
};
