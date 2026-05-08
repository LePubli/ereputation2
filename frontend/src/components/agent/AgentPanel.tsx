import { useState } from 'react';
import { X, Sparkles, Loader2, Send, History } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { apiClient } from '../../api/client';
import type { Prospect } from '../../types';

interface AgentPanelProps {
  prospect: Prospect;
  onClose: () => void;
}

const PROMPT_TEMPLATES = [
  { label: '💰 CA estimé', prompt: 'Estime le chiffre d\'affaires annuel de cette entreprise en euros. Réponds avec une valeur numérique.' },
  { label: '👤 Décideur', prompt: 'Trouve le nom et le titre du principal décideur ou dirigeant de cette entreprise.' },
  { label: '📈 Signaux croissance', prompt: 'Identifie les signaux de croissance récents : recrutements, nouveaux marchés, levées de fonds, expansions.' },
  { label: '🏷️ Positionnement', prompt: 'En 1 phrase, décris le positionnement commercial et les offres principales de cette entreprise.' },
  { label: '🔴 Signaux négatifs', prompt: 'Y a-t-il des signaux négatifs : difficultés financières, mauvaises notes, fermetures de sites ?' },
  { label: '📧 Email probable', prompt: 'Déduis le format probable de l\'email professionnel du dirigeant depuis le domaine web.' },
];

export function AgentPanel({ prospect, onClose }: AgentPanelProps) {
  const [prompt, setPrompt] = useState('');
  const [field, setField] = useState('');
  const [history, setHistory] = useState<{ prompt: string; result: any; field?: string }[]>([]);

  const runMutation = useMutation({
    mutationFn: async ({ prompt, field }: { prompt: string; field: string }) => {
      const { data } = await apiClient.post('/agent/run', {
        prospect_id: prospect.id,
        prompt,
        field: field || null,
        use_search: true,
      });
      return data;
    },
    onSuccess: (data) => {
      setHistory((h) => [{ prompt, result: data, field }, ...h]);
      if (field) toast.success(`Champ "${field}" mis à jour`);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || 'Erreur agent IA';
      toast.error(detail);
    },
  });

  const submit = () => {
    if (!prompt.trim()) return;
    runMutation.mutate({ prompt: prompt.trim(), field: field.trim() });
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-xl bg-white shadow-2xl z-50 flex flex-col border-l">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b bg-gradient-to-r from-purple-50 to-white">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="font-bold text-sm">AI Agent</h2>
            <p className="text-xs text-gray-500 truncate max-w-64">{prospect.company_name}</p>
          </div>
        </div>
        <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Contexte prospect */}
      <div className="px-5 py-3 bg-gray-50 border-b">
        <div className="grid grid-cols-3 gap-2 text-xs">
          <InfoChip label="SIREN" value={prospect.siren || '—'} />
          <InfoChip label="Ville" value={prospect.city || '—'} />
          <InfoChip label="NAF" value={prospect.naf_code || '—'} />
          <InfoChip label="Effectifs" value={prospect.employee_range || '—'} />
          <InfoChip label="Site" value={prospect.website ? '✓' : '—'} />
          <InfoChip label="Score" value={prospect.propensity_score ? `${Math.round(prospect.propensity_score)}/100` : '—'} />
        </div>
      </div>

      {/* Templates */}
      <div className="px-5 py-3 border-b">
        <p className="text-xs text-gray-500 mb-2 font-medium">Prompts rapides</p>
        <div className="flex flex-wrap gap-1.5">
          {PROMPT_TEMPLATES.map((t) => (
            <button key={t.label}
              onClick={() => setPrompt(t.prompt)}
              className="text-xs px-2.5 py-1 bg-purple-50 text-purple-700 border border-purple-100 rounded hover:bg-purple-100 transition">
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Résultats */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
        {history.length === 0 && !runMutation.isPending && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Sparkles className="w-10 h-10 text-purple-200 mb-3" />
            <p className="text-sm text-gray-500">Pose une question sur cette entreprise</p>
            <p className="text-xs text-gray-400 mt-1">L'agent recherche sur le web et synthétise</p>
          </div>
        )}

        {runMutation.isPending && (
          <div className="flex items-center gap-3 p-4 bg-purple-50 rounded-lg border border-purple-100">
            <Loader2 className="w-4 h-4 animate-spin text-purple-600 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-purple-900">Recherche en cours…</p>
              <p className="text-xs text-purple-600 truncate">{prompt}</p>
            </div>
          </div>
        )}

        {history.map((h, idx) => (
          <div key={idx} className="border rounded-lg overflow-hidden">
            <div className="px-3 py-2 bg-gray-50 border-b">
              <p className="text-xs text-gray-500 truncate">{h.prompt}</p>
            </div>
            <div className="px-3 py-3">
              {h.result?.error ? (
                <p className="text-sm text-red-600">{h.result.error}</p>
              ) : (
                <>
                  <div className="flex items-start gap-2 mb-2">
                    <span className="w-2 h-2 rounded-full bg-purple-500 mt-1.5 flex-shrink-0" />
                    <p className="text-sm font-medium text-gray-900">
                      {String(h.result?.result ?? '—')}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-400">
                    <span>Source: {h.result?.source || '—'}</span>
                    <span>Confiance: {Math.round((h.result?.confidence || 0) * 100)}%</span>
                    <span>{h.result?.tokens_used} tokens</span>
                  </div>
                  {h.result?.reasoning && (
                    <p className="text-xs text-gray-500 mt-1.5 italic">{h.result.reasoning}</p>
                  )}
                  {h.field && (
                    <p className="text-xs text-green-600 mt-1">✓ Enregistré dans le champ "{h.field}"</p>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="px-5 py-4 border-t bg-white">
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={field}
            onChange={(e) => setField(e.target.value)}
            placeholder="Champ cible (optionnel: ca_estime)"
            className="flex-1 px-3 py-1.5 text-xs border rounded font-mono"
          />
        </div>
        <div className="flex gap-2">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && e.ctrlKey) submit(); }}
            placeholder="Que veux-tu savoir sur cette entreprise ? (Ctrl+Entrée pour envoyer)"
            rows={3}
            className="flex-1 px-3 py-2 text-sm border rounded resize-none focus:ring-2 focus:ring-purple-500"
          />
          <button
            onClick={submit}
            disabled={!prompt.trim() || runMutation.isPending}
            className="flex-shrink-0 w-10 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center"
          >
            {runMutation.isPending
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Send className="w-4 h-4" />
            }
          </button>
        </div>
      </div>
    </div>
  );
}

function InfoChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white border rounded px-2 py-1">
      <div className="text-gray-400" style={{ fontSize: 10 }}>{label}</div>
      <div className="font-medium text-gray-800 truncate" style={{ fontSize: 11 }}>{value}</div>
    </div>
  );
}
