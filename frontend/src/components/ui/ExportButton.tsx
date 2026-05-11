import { useState, useRef, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { useToast } from './Toast';

interface ExportOption {
  label: string;
  endpoint: string;
  icon: string;
  params?: Record<string, string>;
}

interface Props {
  options?: ExportOption[];
  defaultEndpoint?: string;
  label?: string;
  ids?: string[];
  compact?: boolean;
}

const DEFAULT_OPTIONS: ExportOption[] = [
  { label: 'CSV — Prospects', endpoint: '/prospects/export', icon: '📄' },
  { label: 'Excel — Prospects', endpoint: '/export/prospects.xlsx', icon: '📊' },
  { label: 'Excel — Pipeline', endpoint: '/export/pipeline.xlsx', icon: '📋' },
  { label: 'Rapport complet', endpoint: '/export/full-report.xlsx', icon: '📑' },
];

export default function ExportButton({ options = DEFAULT_OPTIONS, label = 'Exporter', ids, compact = false }: Props) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const toast = useToast();

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const download = async (opt: ExportOption) => {
    setLoading(opt.endpoint);
    setOpen(false);
    const id = toast.loading(`Export ${opt.label}...`, 'Génération du fichier en cours');

    try {
      let url = opt.endpoint;
      const params = new URLSearchParams(opt.params || {});
      if (ids?.length) ids.forEach(i => params.append('ids', i));
      if (params.toString()) url += `?${params}`;

      const blob = await apiClient.getBlob(url);
      const ext = opt.endpoint.endsWith('.xlsx') ? '.xlsx' : '.csv';
      const filename = `export_${new Date().toISOString().slice(0, 10)}${ext}`;

      const href = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = href; a.download = filename; a.click();
      URL.revokeObjectURL(href);

      toast.update(id, { type: 'success', title: `✅ ${opt.label} téléchargé`, message: filename });
    } catch (e) {
      toast.update(id, { type: 'error', title: `❌ Erreur export`, message: String(e) });
    } finally {
      setLoading(null);
    }
  };

  const isLoading = loading !== null;

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setOpen(o => !o)}
        disabled={isLoading}
        style={{
          padding: compact ? '0.375rem 0.625rem' : '0.5rem 0.875rem',
          borderRadius: '8px', cursor: isLoading ? 'not-allowed' : 'pointer',
          background: open ? 'rgba(47,129,247,0.15)' : 'var(--bg-tertiary)',
          border: `1px solid ${open ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
          color: open ? 'var(--accent-blue)' : 'var(--text-secondary)',
          fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '0.375rem',
          transition: 'all 0.15s',
        }}
      >
        {isLoading ? (
          <span style={{
            width: '12px', height: '12px', border: '2px solid currentColor',
            borderTopColor: 'transparent', borderRadius: '50%',
            animation: 'spin 0.7s linear infinite', display: 'inline-block',
          }} />
        ) : '⬇️'}
        {!compact && label}
        {!compact && !isLoading && <span style={{ fontSize: '0.625rem', marginLeft: '2px' }}>▼</span>}
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 6px)', right: 0,
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: '10px', boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          minWidth: '240px', zIndex: 200, overflow: 'hidden',
          animation: 'slideDown 0.15s ease',
        }}>
          <div style={{ padding: '0.375rem 0.75rem 0.25rem', fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Format d'export
          </div>
          {options.map(opt => (
            <button
              key={opt.endpoint}
              onClick={() => download(opt)}
              style={{
                width: '100%', padding: '0.625rem 0.875rem',
                background: 'none', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: '0.75rem',
                color: 'var(--text-secondary)', fontSize: '0.875rem', textAlign: 'left',
                transition: 'all 0.1s',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-secondary)'; (e.currentTarget as HTMLElement).style.color = 'var(--text-primary)'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'none'; (e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)'; }}
            >
              <span style={{ fontSize: '1rem' }}>{opt.icon}</span>
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}
