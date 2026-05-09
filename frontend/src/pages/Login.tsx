import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Lock } from 'lucide-react';
import { toast } from 'sonner';
import { useAuthStore } from '../hooks/useAuth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch {
      toast.error('Identifiants incorrects');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-subtle)' }}>
      <div style={{ width: '100%', maxWidth: 440 }}>
        <div className="card" style={{ padding: 32 }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 32 }}>
            <div style={{ width: 48, height: 48, background: 'linear-gradient(135deg, var(--brand-500), var(--brand-700))', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 18, color: 'white', marginBottom: 12, boxShadow: 'var(--s-md)' }}>
              BP
            </div>
            <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--tx-primary)', marginBottom: 4 }}>B2B Prospector</h1>
            <p style={{ fontSize: 13, color: 'var(--tx-muted)', marginTop: 4 }}>Le Publicitaire — Espace commercial</p>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--tx-secondary)', marginBottom: 6 }}>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="admin@le-publicitaire.fr"
                required
                disabled={loading}
                autoComplete="email"
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--tx-secondary)', marginBottom: 6 }}>Mot de passe</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                required
                disabled={loading}
                autoComplete="current-password"
                style={{ width: '100%' }}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !email || !password}
              className="btn btn-primary"
              style={{ width: '100%', height: 40, marginTop: 8 }}
            >
              {loading ? <Loader2 className="animate-spin" size={16} /> : <Lock size={16} />}
              {loading ? 'Connexion…' : 'Se connecter'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
