interface BulkAction {
  label: string;
  icon: string;
  action: () => void;
  variant?: 'default' | 'danger' | 'success';
  loading?: boolean;
}

interface Props {
  count: number;
  actions: BulkAction[];
  onClear: () => void;
}

export default function BulkActionsBar({ count, actions, onClear }: Props) {
  if (count === 0) return null;

  return (
    <div style={{
      position: 'fixed', bottom: '1.5rem', left: '50%', transform: 'translateX(-50%)',
      zIndex: 500,
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: '12px',
      padding: '0.75rem 1rem',
      display: 'flex', alignItems: 'center', gap: '1rem',
      boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
      backdropFilter: 'blur(8px)',
      minWidth: '500px',
      animation: 'slideUp 0.2s ease',
    }}>
      {/* Count */}
      <div style={{
        padding: '0.25rem 0.75rem', borderRadius: '20px',
        background: 'rgba(47,129,247,0.15)', border: '1px solid rgba(47,129,247,0.3)',
        color: 'var(--accent-blue)', fontSize: '0.875rem', fontWeight: 600,
        flexShrink: 0,
      }}>
        {count} sélectionné{count > 1 ? 's' : ''}
      </div>

      <div style={{ width: '1px', height: '24px', background: 'var(--border-color)', flexShrink: 0 }} />

      {/* Actions */}
      <div style={{ display: 'flex', gap: '0.5rem', flex: 1 }}>
        {actions.map(act => {
          const colors = {
            default: { bg: 'var(--bg-tertiary)', border: 'var(--border-color)', color: 'var(--text-secondary)' },
            danger: { bg: 'rgba(248,81,73,0.1)', border: 'rgba(248,81,73,0.3)', color: 'var(--accent-red)' },
            success: { bg: 'rgba(63,185,80,0.1)', border: 'rgba(63,185,80,0.3)', color: 'var(--accent-green)' },
          }[act.variant || 'default'];

          return (
            <button
              key={act.label}
              onClick={act.action}
              disabled={act.loading}
              style={{
                padding: '0.4375rem 0.875rem', borderRadius: '8px',
                background: colors.bg, border: `1px solid ${colors.border}`,
                color: colors.color, fontSize: '0.8125rem', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: '0.375rem',
                opacity: act.loading ? 0.7 : 1, transition: 'all 0.15s',
                whiteSpace: 'nowrap',
              }}
            >
              {act.loading ? (
                <span style={{
                  width: '12px', height: '12px', border: '2px solid currentColor',
                  borderTopColor: 'transparent', borderRadius: '50%',
                  animation: 'spin 0.7s linear infinite', display: 'inline-block',
                }} />
              ) : act.icon}
              {act.label}
            </button>
          );
        })}
      </div>

      {/* Clear */}
      <button
        onClick={onClear}
        style={{
          background: 'none', border: 'none', color: 'var(--text-muted)',
          cursor: 'pointer', fontSize: '1rem', padding: '0.25rem',
          flexShrink: 0, borderRadius: '4px',
        }}
      >✕</button>

      <style>{`
        @keyframes slideUp { from { opacity: 0; transform: translateX(-50%) translateY(16px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
