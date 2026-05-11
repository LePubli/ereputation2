import { useState } from 'react';
import { apiClient } from '../api/client';

interface SettingSection {
  id: string;
  label: string;
  icon: string;
}

const SECTIONS: SettingSection[] = [
  { id: 'general', label: 'Général', icon: '⚙️' },
  { id: 'smtp', label: 'Email SMTP', icon: '📧' },
  { id: 'ai', label: 'Intelligence IA', icon: '🤖' },
  { id: 'apis', label: 'APIs Contact', icon: '🔌' },
  { id: 'security', label: 'Sécurité', icon: '🔒' },
];

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState('general');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);

  const [settings, setSettings] = useState({
    // General
    company_name: 'Le Publicitaire',
    timezone: 'Europe/Paris',
    language: 'fr',
    results_per_page: '25',
    // SMTP
    smtp_host: 'mail.le-publicitaire.fr',
    smtp_port: '587',
    smtp_user: '',
    smtp_password: '',
    smtp_from: 'contact@le-publicitaire.fr',
    smtp_from_name: 'Le Publicitaire',
    smtp_tls: true,
    // AI
    anthropic_key: '',
    qwen_key: '',
    groq_key: '',
    ollama_url: 'http://localhost:11434',
    ai_default_provider: 'auto',
    // APIs
    hunter_key: '',
    dropcontact_key: '',
    apollo_key: '',
    snovio_client_id: '',
    snovio_secret: '',
    datagma_key: '',
    // Security
    session_timeout: '24',
    two_factor: false,
  });

  const save = async () => {
    setSaving(true);
    try {
      await apiClient.post('/system/settings', settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally { setSaving(false); }
  };

  const testSmtp = async () => {
    setTesting('smtp');
    try {
      await apiClient.post('/system/test-smtp', {
        host: settings.smtp_host,
        port: parseInt(settings.smtp_port),
        user: settings.smtp_user,
        password: settings.smtp_password,
      });
      alert('✅ Connexion SMTP réussie !');
    } catch {
      alert('❌ Échec de connexion SMTP');
    } finally { setTesting(null); }
  };

  const testApi = async (provider: string, key: string) => {
    setTesting(provider);
    try {
      await apiClient.post(`/contacts/test-provider`, { provider, api_key: key });
      alert(`✅ API ${provider} opérationnelle !`);
    } catch {
      alert(`❌ Clé ${provider} invalide`);
    } finally { setTesting(null); }
  };

  const set = (key: keyof typeof settings, value: string | boolean) =>
    setSettings(prev => ({ ...prev, [key]: value }));

  return (
    <div style={{ padding: '1.5rem', display: 'flex', gap: '1.5rem', height: '100%', boxSizing: 'border-box', overflow: 'hidden' }}>

      {/* Sidebar nav */}
      <div style={{
        width: '200px', minWidth: '200px',
        background: 'var(--bg-card)', border: '1px solid var(--border-color)',
        borderRadius: '10px', padding: '0.5rem', height: 'fit-content',
      }}>
        {SECTIONS.map(s => (
          <button
            key={s.id}
            onClick={() => setActiveSection(s.id)}
            style={{
              width: '100%', padding: '0.625rem 0.875rem',
              borderRadius: '8px', border: 'none',
              background: activeSection === s.id ? 'rgba(47,129,247,0.15)' : 'none',
              color: activeSection === s.id ? 'var(--accent-blue)' : 'var(--text-secondary)',
              cursor: 'pointer', fontSize: '0.875rem', textAlign: 'left',
              display: 'flex', alignItems: 'center', gap: '0.625rem',
              fontWeight: activeSection === s.id ? 600 : 400,
              transition: 'all 0.1s',
            }}
          >
            <span>{s.icon}</span> {s.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: '10px', padding: '1.5rem', maxWidth: '700px',
        }}>
          {/* General */}
          {activeSection === 'general' && (
            <Section title="⚙️ Paramètres généraux">
              <Field label="Nom de l'entreprise" value={settings.company_name} onChange={v => set('company_name', v)} />
              <Field label="Fuseau horaire" type="select" value={settings.timezone} onChange={v => set('timezone', v)}
                options={['Europe/Paris', 'Europe/London', 'America/New_York']} />
              <Field label="Résultats par page" type="select" value={settings.results_per_page} onChange={v => set('results_per_page', v)}
                options={['10', '25', '50', '100']} />
            </Section>
          )}

          {/* SMTP */}
          {activeSection === 'smtp' && (
            <Section title="📧 Configuration SMTP" action={
              <button onClick={testSmtp} disabled={testing === 'smtp'} style={secondaryBtn}>
                {testing === 'smtp' ? 'Test...' : '🔌 Tester'}
              </button>
            }>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <Field label="Serveur SMTP" value={settings.smtp_host} onChange={v => set('smtp_host', v)} />
                <Field label="Port" value={settings.smtp_port} onChange={v => set('smtp_port', v)} />
                <Field label="Utilisateur" value={settings.smtp_user} onChange={v => set('smtp_user', v)} />
                <Field label="Mot de passe" type="password" value={settings.smtp_password} onChange={v => set('smtp_password', v)} />
                <Field label="Email expéditeur" value={settings.smtp_from} onChange={v => set('smtp_from', v)} />
                <Field label="Nom expéditeur" value={settings.smtp_from_name} onChange={v => set('smtp_from_name', v)} />
              </div>
              <ToggleField label="Activer TLS/STARTTLS" value={settings.smtp_tls} onChange={v => set('smtp_tls', v)} />
            </Section>
          )}

          {/* AI */}
          {activeSection === 'ai' && (
            <Section title="🤖 Configuration IA multi-providers">
              <InfoBox>
                Le système choisit automatiquement le provider disponible dans l'ordre : Claude → Qwen → Groq → Ollama
              </InfoBox>
              <Field label="Clé API Anthropic (Claude)" type="password" value={settings.anthropic_key} onChange={v => set('anthropic_key', v)} placeholder="sk-ant-..." />
              <Field label="Clé API Qwen (1M tokens/mois gratuit)" type="password" value={settings.qwen_key} onChange={v => set('qwen_key', v)} placeholder="sk-..." />
              <Field label="Clé API Groq (500k tokens/jour gratuit)" type="password" value={settings.groq_key} onChange={v => set('groq_key', v)} placeholder="gsk_..." />
              <Field label="URL Ollama local (gratuit, illimité)" value={settings.ollama_url} onChange={v => set('ollama_url', v)} placeholder="http://localhost:11434" />
              <Field label="Provider par défaut" type="select" value={settings.ai_default_provider} onChange={v => set('ai_default_provider', v)}
                options={['auto', 'claude', 'qwen', 'groq', 'ollama']} />
            </Section>
          )}

          {/* APIs */}
          {activeSection === 'apis' && (
            <Section title="🔌 APIs Contact Intelligence">
              <InfoBox>Toutes les APIs sont optionnelles. Le système utilise les patterns email + vérification SMTP par défaut (gratuit).</InfoBox>
              {[
                { key: 'hunter_key' as const, label: 'Hunter.io', placeholder: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' },
                { key: 'dropcontact_key' as const, label: 'Dropcontact', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' },
                { key: 'apollo_key' as const, label: 'Apollo.io', placeholder: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' },
                { key: 'datagma_key' as const, label: 'Datagma', placeholder: 'api-xxxx' },
              ].map(api => (
                <div key={api.key} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
                  <div style={{ flex: 1 }}>
                    <Field label={api.label} type="password" value={settings[api.key]} onChange={v => set(api.key, v)} placeholder={api.placeholder} />
                  </div>
                  {settings[api.key] && (
                    <button
                      onClick={() => testApi(api.label.toLowerCase().split('.')[0], settings[api.key])}
                      disabled={!!testing}
                      style={{ ...secondaryBtn, marginBottom: '0', alignSelf: 'flex-end', height: '36px' }}
                    >
                      {testing === api.label.toLowerCase().split('.')[0] ? '...' : 'Test'}
                    </button>
                  )}
                </div>
              ))}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <Field label="Snov.io Client ID" type="password" value={settings.snovio_client_id} onChange={v => set('snovio_client_id', v)} />
                <Field label="Snov.io Secret" type="password" value={settings.snovio_secret} onChange={v => set('snovio_secret', v)} />
              </div>
            </Section>
          )}

          {/* Security */}
          {activeSection === 'security' && (
            <Section title="🔒 Sécurité">
              <Field label="Durée de session (heures)" type="select" value={settings.session_timeout} onChange={v => set('session_timeout', v)}
                options={['1', '8', '24', '72', '168']} />
              <ToggleField label="Authentification à deux facteurs (2FA)" value={settings.two_factor} onChange={v => set('two_factor', v)} />
            </Section>
          )}

          {/* Save button */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem', gap: '0.5rem', alignItems: 'center' }}>
            {saved && (
              <span style={{ color: 'var(--accent-green)', fontSize: '0.875rem' }}>✅ Enregistré</span>
            )}
            <button
              onClick={save}
              disabled={saving}
              style={{
                padding: '0.625rem 1.5rem', borderRadius: '8px',
                background: 'var(--accent-blue)', border: 'none',
                color: '#fff', cursor: 'pointer', fontSize: '0.875rem',
                fontWeight: 600, opacity: saving ? 0.7 : 1,
              }}
            >{saving ? 'Enregistrement...' : 'Enregistrer les modifications'}</button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Sub-components ---------- */

const secondaryBtn: React.CSSProperties = {
  padding: '0.4375rem 0.875rem', borderRadius: '8px',
  background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
  color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.8125rem',
};

function Section({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>{title}</h2>
        {action}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
        {children}
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', options, placeholder }: {
  label: string; value: string; onChange: (v: string) => void;
  type?: 'text' | 'password' | 'select'; options?: string[]; placeholder?: string;
}) {
  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '0.5625rem 0.875rem',
    background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
    borderRadius: '8px', color: 'var(--text-primary)', fontSize: '0.875rem',
    outline: 'none', boxSizing: 'border-box',
  };
  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>{label}</label>
      {type === 'select' ? (
        <select value={value} onChange={e => onChange(e.target.value)} style={inputStyle}>
          {options?.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : (
        <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} style={inputStyle} />
      )}
    </div>
  );
}

function ToggleField({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{label}</span>
      <button
        onClick={() => onChange(!value)}
        style={{
          width: '44px', height: '24px', borderRadius: '12px', border: 'none', cursor: 'pointer',
          background: value ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
          position: 'relative', transition: 'background 0.2s',
        }}
      >
        <div style={{
          position: 'absolute', top: '3px', left: value ? '23px' : '3px',
          width: '18px', height: '18px', borderRadius: '50%', background: '#fff',
          transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
        }} />
      </button>
    </div>
  );
}

function InfoBox({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      background: 'rgba(47,129,247,0.08)', border: '1px solid rgba(47,129,247,0.2)',
      borderRadius: '8px', padding: '0.75rem 1rem',
      color: 'var(--text-secondary)', fontSize: '0.8125rem', lineHeight: 1.5,
    }}>
      ℹ️ {children}
    </div>
  );
}
