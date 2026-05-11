import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch {
      setError('Email ou mot de passe incorrect');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
    }}>
      {/* Background grid */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0,
        backgroundImage: 'radial-gradient(circle at 1px 1px, var(--border-color) 1px, transparent 0)',
        backgroundSize: '32px 32px',
        opacity: 0.4,
        pointerEvents: 'none',
      }} />

      {/* Glow */}
      <div style={{
        position: 'fixed', top: '-200px', left: '50%', transform: 'translateX(-50%)',
        width: '600px', height: '600px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(47,129,247,0.12) 0%, transparent 70%)',
        pointerEvents: 'none', zIndex: 0,
      }} />

      <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: '400px' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.75rem',
            marginBottom: '0.75rem',
          }}>
            <div style={{
              width: '40px', height: '40px', borderRadius: '10px',
              background: 'linear-gradient(135deg, var(--accent-blue), #7c3aed)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.25rem',
            }}>⚡</div>
            <span style={{
              fontSize: '1.375rem', fontWeight: 700,
              color: 'var(--text-primary)', letterSpacing: '-0.02em',
            }}>B2B Prospector</span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Le Publicitaire — Intelligence Commerciale
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '2rem',
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        }}>
          <h1 style={{
            fontSize: '1.125rem', fontWeight: 600,
            color: 'var(--text-primary)', marginBottom: '1.5rem',
          }}>
            Connexion
          </h1>

          {error && (
            <div style={{
              background: 'rgba(248,81,73,0.1)', border: '1px solid rgba(248,81,73,0.3)',
              borderRadius: '8px', padding: '0.75rem 1rem',
              color: 'var(--accent-red)', fontSize: '0.875rem',
              marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem',
            }}>
              <span>⚠️</span> {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{
                display: 'block', fontSize: '0.8125rem', fontWeight: 500,
                color: 'var(--text-secondary)', marginBottom: '0.5rem',
              }}>
                Adresse email
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin@le-publicitaire.fr"
                required
                style={{
                  width: '100%', padding: '0.625rem 0.875rem',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px', color: 'var(--text-primary)',
                  fontSize: '0.875rem', outline: 'none',
                  transition: 'border-color 0.15s',
                  boxSizing: 'border-box',
                }}
                onFocus={e => e.target.style.borderColor = 'var(--accent-blue)'}
                onBlur={e => e.target.style.borderColor = 'var(--border-color)'}
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{
                display: 'block', fontSize: '0.8125rem', fontWeight: 500,
                color: 'var(--text-secondary)', marginBottom: '0.5rem',
              }}>
                Mot de passe
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: '100%', padding: '0.625rem 0.875rem',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px', color: 'var(--text-primary)',
                  fontSize: '0.875rem', outline: 'none',
                  transition: 'border-color 0.15s',
                  boxSizing: 'border-box',
                }}
                onFocus={e => e.target.style.borderColor = 'var(--accent-blue)'}
                onBlur={e => e.target.style.borderColor = 'var(--border-color)'}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%', padding: '0.75rem',
                background: loading ? 'var(--bg-tertiary)' : 'var(--accent-blue)',
                border: 'none', borderRadius: '8px',
                color: '#fff', fontSize: '0.875rem', fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
              }}
            >
              {loading ? (
                <>
                  <span style={{
                    width: '14px', height: '14px', border: '2px solid rgba(255,255,255,0.3)',
                    borderTopColor: '#fff', borderRadius: '50%',
                    animation: 'spin 0.7s linear infinite', display: 'inline-block',
                  }} />
                  Connexion...
                </>
              ) : 'Se connecter →'}
            </button>
          </form>
        </div>

        <p style={{
          textAlign: 'center', marginTop: '1.5rem',
          color: 'var(--text-muted)', fontSize: '0.75rem',
        }}>
          B2B Prospector v2.0 · Le Publicitaire © 2025
        </p>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        input::placeholder { color: var(--text-muted); }
      `}</style>
    </div>
  );
}
