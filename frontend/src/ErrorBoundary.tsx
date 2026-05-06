import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * ErrorBoundary global — capture les crashes runtime React et affiche un
 * message clair au lieu de laisser l'écran noir (page non rendue).
 *
 * Sans ce composant, une exception dans n'importe quel descendant fait que
 * React démonte tout l'arbre et le <div id="root"></div> reste vide, ce qui
 * donne l'impression d'un "écran noir" en production.
 */
export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log dans la console (visible dans DevTools) + Sentry si configuré
    console.error('[ErrorBoundary] Crash React capturé:', error, errorInfo);
    this.setState({ errorInfo });

    // Hook Sentry si DSN défini au build
    const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
    if (sentryDsn && (window as unknown as { Sentry?: { captureException: (e: Error) => void } }).Sentry) {
      (window as unknown as { Sentry: { captureException: (e: Error) => void } }).Sentry.captureException(error);
    }
  }

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#111827',
          color: '#f3f4f6',
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
          padding: '2rem',
        }}
      >
        <div
          style={{
            maxWidth: '640px',
            width: '100%',
            backgroundColor: '#1f2937',
            border: '1px solid #374151',
            borderRadius: '12px',
            padding: '2rem',
            boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <span style={{ fontSize: '2rem' }}>⚠️</span>
            <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>
              Une erreur est survenue
            </h1>
          </div>

          <p style={{ color: '#9ca3af', lineHeight: 1.6, marginBottom: '1.5rem' }}>
            L'application a rencontré une erreur inattendue. Vous pouvez recharger la page pour
            réessayer. Si le problème persiste, contactez le support technique.
          </p>

          {this.state.error && (
            <details
              style={{
                backgroundColor: '#111827',
                border: '1px solid #374151',
                borderRadius: '8px',
                padding: '1rem',
                marginBottom: '1.5rem',
              }}
            >
              <summary
                style={{
                  cursor: 'pointer',
                  fontWeight: 600,
                  color: '#fbbf24',
                  marginBottom: '0.5rem',
                }}
              >
                Détails techniques
              </summary>
              <pre
                style={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontSize: '0.8rem',
                  color: '#d1d5db',
                  margin: 0,
                  marginTop: '0.5rem',
                  fontFamily: 'ui-monospace, "SF Mono", Menlo, monospace',
                }}
              >
                {this.state.error.toString()}
                {this.state.errorInfo?.componentStack}
              </pre>
            </details>
          )}

          <button
            type="button"
            onClick={this.handleReload}
            style={{
              backgroundColor: '#2563eb',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background 0.15s',
            }}
            onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#1d4ed8')}
            onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#2563eb')}
          >
            Recharger la page
          </button>
        </div>
      </div>
    );
  }
}
