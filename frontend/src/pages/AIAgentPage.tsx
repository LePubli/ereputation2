import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Send, Loader2, Sparkles, Zap, Bot, ChevronDown, Copy, CheckCheck, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '../api/client';
import { PageHeader } from '../components/layout/AppShell';

const PROVIDERS = [
  { id: 'auto',   label: 'Auto (meilleur dispo)', icon: '⚡' },
  { id: 'claude', label: 'Claude Sonnet',          icon: '🧠' },
  { id: 'qwen',   label: 'Qwen Turbo (gratuit)',   icon: '🌐' },
  { id: 'groq',   label: 'Llama 3.3 / Groq',       icon: '🚀' },
  { id: 'ollama', label: 'Ollama (local)',           icon: '🏠' },
];

const MODES = [
  { id: 'agent',    label: 'Agent',    desc: 'Recherche & collecte' },
  { id: 'email',    label: 'Email',    desc: 'Rédaction email B2B' },
  { id: 'scoring',  label: 'Scoring',  desc: 'Qualification prospect' },
  { id: 'research', label: 'Research', desc: 'Analyse approfondie' },
  { id: 'extract',  label: 'Extract',  desc: 'Extraction données' },
];

const TEMPLATES = [
  { icon: '💰', label: 'CA estimé',          prompt: 'Estime le chiffre d\'affaires annuel en euros. Retourne une valeur numérique dans result.' },
  { icon: '👤', label: 'Décideur',            prompt: 'Trouve le nom complet et le titre exact du dirigeant principal. Inclus son LinkedIn si trouvable.' },
  { icon: '📈', label: 'Signaux croissance',  prompt: 'Identifie les 3 principaux signaux de croissance récents (recrutements, nouveaux marchés, levée de fonds, expansion).' },
  { icon: '🏷️', label: 'Positionnement',      prompt: 'Décris en 2 phrases le positionnement et les offres principales de l\'entreprise.' },
  { icon: '🎯', label: 'Angle de vente',       prompt: 'Identifie le meilleur angle pour proposer des services digitaux (web, SEO, automatisation). Sois très spécifique.' },
  { icon: '❌', label: 'Signaux négatifs',      prompt: 'Y a-t-il des signaux négatifs : difficultés, mauvaises avis, contentieux, procédures ? Sois factuel.' },
  { icon: '📧', label: 'Email pattern',        prompt: 'Déduis le format probable d\'email du dirigeant depuis le domaine web (ex: prenom.nom@domaine.fr).' },
  { icon: '🔍', label: 'Concurrents',         prompt: 'Identifie les 3 principaux concurrents de cette entreprise dans son secteur géographique.' },
];

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  provider?: string;
  model?: string;
  tokens?: number;
  duration?: number;
  cost?: number;
  json?: any;
  error?: boolean;
}

export default function AIAgentPage() {
  const [provider, setProvider] = useState('auto');
  const [mode, setMode] = useState('agent');
  const [useSearch, setUseSearch] = useState(true);
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [copied, setCopied] = useState<string | null>(null);
  const [showProviders, setShowProviders] = useState(false);

  const { data: availableProviders } = useQuery({
    queryKey: ['ai-providers'],
    queryFn: async () => { const { data } = await apiClient.get('/ai/providers'); return data.providers; },
    staleTime: 60_000,
  });

  const mutation = useMutation({
    mutationFn: async (p: string) => {
      const { data } = await apiClient.post('/ai/complete', {
        prompt: p, mode, provider, use_search: useSearch, max_tokens: 2000,
      });
      return data;
    },
    onSuccess: (data, vars) => {
      setMessages(prev => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.content,
          provider: data.provider,
          model: data.model,
          tokens: data.tokens_total,
          duration: data.duration_ms,
          cost: data.cost_usd,
          json: data.json_parsed,
        }
      ]);
    },
    onError: () => {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Erreur : aucun provider AI disponible. Configurez QWEN_API_KEY (gratuit) dans Coolify.',
        error: true,
      }]);
    },
  });

  const submit = () => {
    if (!prompt.trim() || mutation.isPending) return;
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: prompt };
    setMessages(prev => [...prev, userMsg]);
    mutation.mutate(prompt);
    setPrompt('');
  };

  const copyContent = (id: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const activeProviderLabel = PROVIDERS.find(p => p.id === provider)?.label || 'Auto';
  const activeModeLabel = MODES.find(m => m.id === mode)?.label || 'Agent';

  return (
    <div className="app-page" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <PageHeader
        title="AI Agent"
        description="Intelligence artificielle multi-provider"
        actions={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {/* Provider selector */}
            <div style={{ position: 'relative' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowProviders(v => !v)}
                style={{ gap: 6 }}>
                <span>{PROVIDERS.find(p => p.id === provider)?.icon}</span>
                <span>{activeProviderLabel}</span>
                <ChevronDown size={12} />
              </button>
              {showProviders && (
                <div style={{
                  position: 'absolute', right: 0, top: '100%', marginTop: 4,
                  background: 'var(--bg-card)', border: '1px solid var(--border)',
                  borderRadius: 10, boxShadow: 'var(--s-lg)', zIndex: 50, minWidth: 220, padding: 6,
                }}>
                  {PROVIDERS.map(p => {
                    const info = availableProviders?.find((ap: any) => ap.id === p.id);
                    const isActive = info?.active || p.id === 'auto';
                    return (
                      <button key={p.id} onClick={() => { setProvider(p.id); setShowProviders(false); }}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '8px 10px',
                          borderRadius: 7, background: provider === p.id ? 'var(--brand-50)' : 'none',
                          border: 'none', cursor: 'pointer', textAlign: 'left', transition: 'background 0.1s',
                        }}
                        onMouseEnter={e => { if (provider !== p.id) e.currentTarget.style.background = 'var(--bg-subtle)'; }}
                        onMouseLeave={e => { if (provider !== p.id) e.currentTarget.style.background = 'transparent'; }}
                      >
                        <span style={{ fontSize: 16 }}>{p.icon}</span>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 13, fontWeight: 500, color: provider === p.id ? 'var(--brand-700)' : 'var(--tx-primary)' }}>{p.label}</div>
                          {info && (
                            <div style={{ fontSize: 10, color: 'var(--tx-muted)' }}>
                              {isActive ? (info.free ? '✓ Gratuit disponible' : '✓ Connecté') : `→ ${info.env_key}`}
                            </div>
                          )}
                        </div>
                        {isActive && <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--c-green)', flexShrink: 0 }} />}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Mode selector */}
            <div style={{ display: 'flex', gap: 2, background: 'var(--bg-subtle)', border: '1px solid var(--border)', borderRadius: 8, padding: 2 }}>
              {MODES.map(m => (
                <button key={m.id} onClick={() => setMode(m.id)}
                  data-tooltip={m.desc}
                  style={{
                    padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 500,
                    border: 'none', cursor: 'pointer', transition: 'all 0.1s',
                    background: mode === m.id ? 'var(--bg-card)' : 'transparent',
                    color: mode === m.id ? 'var(--brand)' : 'var(--tx-muted)',
                    boxShadow: mode === m.id ? 'var(--s-xs)' : 'none',
                  }}>
                  {m.label}
                </button>
              ))}
            </div>

            {/* Search toggle */}
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--tx-secondary)', cursor: 'pointer' }}>
              <input type="checkbox" checked={useSearch} onChange={e => setUseSearch(e.target.checked)}
                style={{ accentColor: 'var(--brand)', width: 13, height: 13 }} />
              Web search
            </label>

            {messages.length > 0 && (
              <button className="btn btn-ghost btn-sm" onClick={() => setMessages([])}>
                <RotateCcw size={13} />
              </button>
            )}
          </div>
        }
      />

      {/* Templates */}
      <div style={{
        padding: '10px 20px', background: 'var(--bg-card)', borderBottom: '1px solid var(--border)',
        display: 'flex', gap: 6, overflowX: 'auto', flexShrink: 0,
      }}>
        {TEMPLATES.map(t => (
          <button key={t.label} onClick={() => setPrompt(t.prompt)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '5px 12px',
              borderRadius: 99, fontSize: 12, fontWeight: 500, whiteSpace: 'nowrap',
              background: 'var(--bg-subtle)', border: '1px solid var(--border)',
              color: 'var(--tx-secondary)', cursor: 'pointer', transition: 'all 0.1s',
              flexShrink: 0,
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--brand-300)'; e.currentTarget.style.color = 'var(--brand)'; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--tx-secondary)'; }}
          >
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        {messages.length === 0 && (
          <div className="empty-state" style={{ flex: 1, justifyContent: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>✦</div>
            <div className="empty-title">AI Agent prêt</div>
            <div className="empty-desc">
              Posez une question sur n'importe quelle entreprise.<br />
              Choisissez un template ci-dessus ou rédigez votre propre requête.<br />
              <strong>Provider actuel : {activeProviderLabel}</strong>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', gap: 0,
            alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '80%',
            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
          }}>
            {msg.role === 'user' ? (
              <div style={{
                background: 'var(--brand)', color: 'white',
                padding: '10px 16px', borderRadius: '16px 16px 4px 16px',
                fontSize: 14, lineHeight: 1.5,
              }}>
                {msg.content}
              </div>
            ) : (
              <div style={{ width: '100%' }}>
                {/* Provider badge */}
                {msg.provider && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <span className={`ai-badge ${msg.provider === 'qwen' ? 'ai-provider-qwen' : msg.provider === 'claude' ? 'ai-provider-claude' : ''}`}>
                      {PROVIDERS.find(p => p.id === msg.provider)?.icon} {msg.provider}
                    </span>
                    <span style={{ fontSize: 11, color: 'var(--tx-muted)' }}>
                      {msg.model} · {msg.tokens} tokens · {msg.duration}ms
                      {msg.cost ? ` · $${msg.cost?.toFixed(5)}` : ' · gratuit'}
                    </span>
                  </div>
                )}

                <div style={{
                  background: msg.error ? 'var(--bg-red)' : 'var(--bg-card)',
                  border: `1px solid ${msg.error ? 'var(--br-red)' : 'var(--border)'}`,
                  borderRadius: '4px 16px 16px 16px',
                  padding: '14px 16px',
                  boxShadow: 'var(--s-xs)',
                  position: 'relative',
                }}>
                  {/* JSON view */}
                  {msg.json && (
                    <div style={{ marginBottom: 12 }}>
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8,
                        padding: '8px 12px', background: 'var(--bg-subtle)',
                        borderRadius: 8, border: '1px solid var(--border)',
                      }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--brand)' }}>
                            {String(msg.json.result ?? '—')}
                          </div>
                          {msg.json.confidence && (
                            <div style={{ fontSize: 11, color: 'var(--tx-muted)', marginTop: 2 }}>
                              Confiance : {Math.round(msg.json.confidence * 100)}%
                            </div>
                          )}
                        </div>
                        {msg.json.confidence && (
                          <div className="progress-wrap" style={{ width: 60 }}>
                            <div className="progress-bar progress-purple" style={{ width: `${msg.json.confidence * 100}%` }} />
                          </div>
                        )}
                      </div>
                      {msg.json.reasoning && (
                        <p style={{ fontSize: 12, color: 'var(--tx-secondary)', fontStyle: 'italic', marginBottom: 0 }}>
                          {msg.json.reasoning}
                        </p>
                      )}
                    </div>
                  )}

                  <p style={{ fontSize: 13, lineHeight: 1.7, color: msg.error ? 'var(--c-red)' : 'var(--tx-primary)', margin: 0, whiteSpace: 'pre-wrap' }}>
                    {msg.json ? msg.content : msg.content}
                  </p>

                  {/* Copy button */}
                  {!msg.error && (
                    <button onClick={() => copyContent(msg.id, msg.content)}
                      style={{
                        position: 'absolute', top: 10, right: 10,
                        background: 'var(--bg-subtle)', border: '1px solid var(--border)',
                        borderRadius: 6, padding: '3px 6px', cursor: 'pointer',
                        color: 'var(--tx-muted)', display: 'flex', alignItems: 'center', gap: 4,
                        fontSize: 11, transition: 'all 0.1s',
                      }}
                    >
                      {copied === msg.id ? <CheckCheck size={11} style={{ color: 'var(--c-green)' }} /> : <Copy size={11} />}
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {mutation.isPending && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 16px',
            background: 'var(--bg-subtle)', border: '1px solid var(--border)',
            borderRadius: '4px 16px 16px 16px', maxWidth: '60%',
          }}>
            <Loader2 size={16} className="animate-spin" style={{ color: 'var(--brand)' }} />
            <div>
              <div style={{ fontSize: 13, fontWeight: 500 }}>Génération en cours…</div>
              <div style={{ fontSize: 11, color: 'var(--tx-muted)' }}>{activeProviderLabel} · mode {activeModeLabel}</div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding: '16px 20px', background: 'var(--bg-card)', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <textarea
              className="textarea"
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); } }}
              placeholder={`Message pour l'agent (mode ${activeModeLabel}) — Entrée pour envoyer, Shift+Entrée pour nouvelle ligne…`}
              rows={3}
              style={{ paddingRight: 12, resize: 'none', borderRadius: 10 }}
            />
          </div>
          <button className="btn btn-primary" onClick={submit}
            disabled={!prompt.trim() || mutation.isPending}
            style={{ height: 80, width: 46, flexDirection: 'column', gap: 4, borderRadius: 10, padding: 0 }}>
            {mutation.isPending
              ? <Loader2 size={16} className="animate-spin" />
              : <Send size={16} />
            }
          </button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 8 }}>
          <span style={{ fontSize: 11, color: 'var(--tx-muted)' }}>
            ↵ Envoyer · ⇧↵ Nouvelle ligne · ⌘K Commandes
          </span>
          <span style={{ fontSize: 11, color: 'var(--tx-muted)' }}>
            {messages.filter(m => m.role === 'assistant').reduce((t, m) => t + (m.tokens || 0), 0)} tokens utilisés
          </span>
        </div>
      </div>
    </div>
  );
}
