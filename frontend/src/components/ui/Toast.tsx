/**
 * Toast Notification System — B2B Prospector
 * - Toasts locaux (succès/erreur/info/warning)
 * - WebSocket temps réel (signaux, enrichissements, syncs)
 * - Persist en mémoire, disparaissent après N secondes
 */
import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';

/* ──────────────────── Types */
export type ToastType = 'success' | 'error' | 'warning' | 'info' | 'loading';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number; // ms, 0 = persistent
  action?: { label: string; onClick: () => void };
  progress?: number; // 0-100, for loading toasts
}

/* ──────────────────── Context */
interface ToastContextValue {
  toasts: Toast[];
  toast: {
    success: (title: string, message?: string) => string;
    error: (title: string, message?: string) => string;
    warning: (title: string, message?: string) => string;
    info: (title: string, message?: string) => string;
    loading: (title: string, message?: string) => string;
    update: (id: string, patch: Partial<Toast>) => void;
    dismiss: (id: string) => void;
    dismissAll: () => void;
  };
}

const ToastContext = createContext<ToastContextValue | null>(null);

/* ──────────────────── Provider */
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const wsRef = useRef<WebSocket | null>(null);

  const add = useCallback((toast: Omit<Toast, 'id'>): string => {
    const id = Math.random().toString(36).slice(2);
    const newToast: Toast = { ...toast, id, duration: toast.duration ?? 4500 };
    setToasts(prev => [...prev.slice(-4), newToast]); // Max 5 visible

    if (newToast.duration && newToast.duration > 0) {
      const timer = setTimeout(() => dismiss(id), newToast.duration);
      timers.current.set(id, timer);
    }
    return id;
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
    const timer = timers.current.get(id);
    if (timer) { clearTimeout(timer); timers.current.delete(id); }
  }, []);

  const update = useCallback((id: string, patch: Partial<Toast>) => {
    setToasts(prev => prev.map(t => t.id === id ? { ...t, ...patch } : t));

    // If updating to non-loading, start dismiss timer
    if (patch.type && patch.type !== 'loading') {
      const timer = timers.current.get(id);
      if (timer) clearTimeout(timer);
      const newTimer = setTimeout(() => dismiss(id), patch.duration ?? 4500);
      timers.current.set(id, newTimer);
    }
  }, [dismiss]);

  // WebSocket connection for real-time notifications
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/notifications?token=${token}`;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            const { type, title, message, data: _data } = msg;
            if (type === 'signal') add({ type: 'info', title: `⚡ ${title}`, message, duration: 6000 });
            else if (type === 'enrich_complete') add({ type: 'success', title: `✅ ${title}`, message, duration: 5000 });
            else if (type === 'sync_complete') add({ type: 'success', title: `🔄 ${title}`, message, duration: 5000 });
            else if (type === 'error') add({ type: 'error', title: `❌ ${title}`, message, duration: 7000 });
            else if (type === 'job_progress') {
              // handled by jobs themselves
            }
          } catch { }
        };

        ws.onclose = () => {
          // Reconnect after 5s
          setTimeout(connect, 5000);
        };

        ws.onerror = () => ws.close();
      } catch { }
    };

    connect();
    return () => { wsRef.current?.close(); };
  }, []);

  const toast = {
    success: (title: string, msg?: string) => add({ type: 'success', title, message: msg }),
    error: (title: string, msg?: string) => add({ type: 'error', title, message: msg, duration: 7000 }),
    warning: (title: string, msg?: string) => add({ type: 'warning', title, message: msg }),
    info: (title: string, msg?: string) => add({ type: 'info', title, message: msg }),
    loading: (title: string, msg?: string) => add({ type: 'loading', title, message: msg, duration: 0 }),
    update,
    dismiss,
    dismissAll: () => setToasts([]),
  };

  return (
    <ToastContext.Provider value={{ toasts, toast }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  );
}

/* ──────────────────── Hook */
export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside ToastProvider');
  return ctx.toast;
}

/* ──────────────────── Container (renders toasts) */
function ToastContainer() {
  const ctx = useContext(ToastContext);
  if (!ctx) return null;
  const { toasts, toast } = ctx;

  return (
    <div style={{
      position: 'fixed', bottom: '1.5rem', right: '1.5rem',
      zIndex: 9999, display: 'flex', flexDirection: 'column',
      gap: '0.5rem', alignItems: 'flex-end',
      pointerEvents: 'none',
    }}>
      {toasts.map(t => (
        <ToastItem key={t.id} toast={t} onDismiss={() => toast.dismiss(t.id)} />
      ))}
    </div>
  );
}

/* ──────────────────── Toast Item */
const TOAST_CONFIG: Record<ToastType, { icon: string; color: string; bg: string; border: string }> = {
  success: { icon: '✅', color: '#3fb950', bg: 'rgba(63,185,80,0.12)', border: 'rgba(63,185,80,0.3)' },
  error: { icon: '❌', color: '#f85149', bg: 'rgba(248,81,73,0.12)', border: 'rgba(248,81,73,0.3)' },
  warning: { icon: '⚠️', color: '#d29922', bg: 'rgba(210,153,34,0.12)', border: 'rgba(210,153,34,0.3)' },
  info: { icon: 'ℹ️', color: '#2f81f7', bg: 'rgba(47,129,247,0.12)', border: 'rgba(47,129,247,0.3)' },
  loading: { icon: '⏳', color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)', border: 'rgba(139,92,246,0.3)' },
};

function ToastItem({ toast: t, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  const [visible, setVisible] = useState(false);
  const cfg = TOAST_CONFIG[t.type];

  useEffect(() => {
    // Animate in
    requestAnimationFrame(() => setVisible(true));
  }, []);

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${cfg.border}`,
        borderLeft: `4px solid ${cfg.color}`,
        borderRadius: '10px',
        padding: '0.875rem 1rem',
        minWidth: '300px', maxWidth: '420px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        pointerEvents: 'all',
        cursor: 'default',
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateX(0)' : 'translateX(24px)',
        transition: 'all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)',
        backdropFilter: 'blur(8px)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.625rem' }}>
        {/* Icon */}
        <div style={{ flexShrink: 0, marginTop: '1px' }}>
          {t.type === 'loading' ? (
            <span style={{
              display: 'inline-block', width: '16px', height: '16px',
              border: `2px solid ${cfg.color}44`,
              borderTopColor: cfg.color, borderRadius: '50%',
              animation: 'spin 0.7s linear infinite',
            }} />
          ) : (
            <span style={{ fontSize: '1rem' }}>{cfg.icon}</span>
          )}
        </div>

        {/* Content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem', lineHeight: 1.3 }}>
            {t.title}
          </div>
          {t.message && (
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', marginTop: '0.125rem', lineHeight: 1.4 }}>
              {t.message}
            </div>
          )}
          {/* Progress bar (for loading/progress toasts) */}
          {t.progress !== undefined && (
            <div style={{ marginTop: '0.5rem', height: '4px', background: 'var(--bg-tertiary)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{
                height: '100%', background: cfg.color, borderRadius: '2px',
                width: `${t.progress}%`, transition: 'width 0.3s ease',
              }} />
            </div>
          )}
          {/* Action button */}
          {t.action && (
            <button
              onClick={t.action.onClick}
              style={{
                marginTop: '0.5rem', padding: '0.25rem 0.75rem', borderRadius: '6px',
                background: `${cfg.color}22`, border: `1px solid ${cfg.color}44`,
                color: cfg.color, fontSize: '0.75rem', cursor: 'pointer', fontWeight: 600,
              }}
            >
              {t.action.label}
            </button>
          )}
        </div>

        {/* Dismiss */}
        <button
          onClick={onDismiss}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-muted)', fontSize: '0.875rem',
            padding: '0.125rem', borderRadius: '4px', flexShrink: 0,
            lineHeight: 1,
          }}
          onMouseEnter={e => (e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)'}
          onMouseLeave={e => (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)'}
        >✕</button>
      </div>
    </div>
  );
}
