import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Mail, Play, Pause, Trash2, BarChart3, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '../api/client';
import { PageHeader } from '../components/layout/AppShell';
import { EmptyState } from '../components/ui/EmptyState';

// --- Types ---
interface Step { step_number: number; wait_days: number; subject_template: string; body_template: string; use_ai_personalization: boolean; ai_personalization_prompt?: string; }
interface Sequence { id: string; name: string; description: string | null; is_active: boolean; created_at: string; }

const TEMPLATE_VARIABLES = ['company_name', 'city', 'naf_label', 'first_name', 'last_name', 'website', 'phone', 'siren'];

const DEFAULT_STEPS: Step[] = [
  {
    step_number: 1, wait_days: 0,
    subject_template: "{{company_name}} — Bonjour depuis Le Publicitaire",
    body_template: `<p>Bonjour,</p>
<p>J'ai découvert <strong>{{company_name}}</strong> basée à {{city}} et je voulais me présenter.</p>
<p>Nous accompagnons les entreprises comme la vôtre sur leur présence digitale et leur référencement.</p>
<p>Seriez-vous disponible pour un appel de 15 minutes cette semaine ?</p>
<p>Cordialement</p>`,
    use_ai_personalization: false,
  },
  {
    step_number: 2, wait_days: 3,
    subject_template: "Re: {{company_name}} — Petite relance",
    body_template: `<p>Bonjour,</p>
<p>Je reviens vers vous suite à mon précédent message concernant <strong>{{company_name}}</strong>.</p>
<p>Avez-vous eu l'occasion d'y jeter un œil ?</p>
<p>Cordialement</p>`,
    use_ai_personalization: true,
    ai_personalization_prompt: "Personnalise ce message de relance en mentionnant un détail spécifique sur l'entreprise (secteur, ville, taille). Garde le même ton professionnel.",
  },
  {
    step_number: 3, wait_days: 7,
    subject_template: "Dernier message — {{company_name}}",
    body_template: `<p>Bonjour,</p>
<p>C'est mon dernier message. Si le moment n'est pas idéal, pas de souci.</p>
<p>N'hésitez pas à revenir vers moi quand vous souhaitez.</p>
<p>Bonne continuation à vous et à <strong>{{company_name}}</strong>.</p>`,
    use_ai_personalization: false,
  },
];

export default function SequencerPage() {
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', steps: DEFAULT_STEPS });
  const [activeStep, setActiveStep] = useState(0);

  const { data: sequences, isLoading } = useQuery<Sequence[]>({
    queryKey: ['sequences'],
    queryFn: async () => { const { data } = await apiClient.get('/sequences'); return data; },
  });

  const createMutation = useMutation({
    mutationFn: (body: typeof form) => apiClient.post('/sequences', body),
    onSuccess: () => { toast.success('Séquence créée'); qc.invalidateQueries({ queryKey: ['sequences'] }); setShowCreate(false); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/sequences/${id}`),
    onSuccess: () => { toast.success('Supprimée'); qc.invalidateQueries({ queryKey: ['sequences'] }); },
  });

  const pauseMutation = useMutation({
    mutationFn: (id: string) => apiClient.post(`/sequences/${id}/pause`),
    onSuccess: () => { toast.success('Séquence pausée'); qc.invalidateQueries({ queryKey: ['sequences'] }); },
  });

  const currentStep = form.steps[activeStep];
  const updateStep = (updates: Partial<Step>) => {
    setForm(f => ({ ...f, steps: f.steps.map((s, i) => i === activeStep ? { ...s, ...updates } : s) }));
  };

  return (
    <>
      <PageHeader
        title="Séquenceur Email"
        description="Séquences multi-étapes avec personnalisation IA — Clay Sequencer"
        actions={
          <button onClick={() => setShowCreate(v => !v)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
            <Plus className="w-4 h-4" /> Nouvelle séquence
          </button>
        }
      />
      <div className="p-6 space-y-4">
        {/* Constructeur de séquence */}
        {showCreate && (
          <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b bg-gray-50 flex items-center justify-between">
              <h3 className="font-semibold">Nouvelle séquence email</h3>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="p-6 grid grid-cols-3 gap-6">
              {/* Config */}
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium mb-1">Nom de la séquence</label>
                  <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                    placeholder="Prospection PME Nord" className="w-full px-3 py-2 text-sm border rounded" />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">Description</label>
                  <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                    rows={2} className="w-full px-3 py-2 text-sm border rounded resize-none" />
                </div>
                <div>
                  <p className="text-xs font-medium mb-2">Étapes ({form.steps.length})</p>
                  <div className="space-y-1">
                    {form.steps.map((s, i) => (
                      <button key={i} onClick={() => setActiveStep(i)}
                        className={`w-full text-left px-3 py-2 rounded text-xs transition ${activeStep === i ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-gray-50 hover:bg-gray-100'}`}>
                        <div className="font-medium">Étape {s.step_number}</div>
                        <div className="text-gray-500">{s.wait_days === 0 ? 'Immédiat' : `J+${s.wait_days}`} {s.use_ai_personalization && '✨'}</div>
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-medium mb-1">Variables disponibles</p>
                  <div className="flex flex-wrap gap-1">
                    {TEMPLATE_VARIABLES.map(v => (
                      <span key={v} className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded font-mono">
                        {`{{${v}}}`}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Éditeur d'étape */}
              <div className="col-span-2 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">Délai après étape précédente</label>
                    <div className="flex items-center gap-2">
                      <input type="number" value={currentStep?.wait_days} min={0}
                        onChange={e => updateStep({ wait_days: Number(e.target.value) })}
                        className="w-20 px-2 py-1.5 text-sm border rounded" />
                      <span className="text-sm text-gray-500">jour(s)</span>
                    </div>
                  </div>
                  <div className="flex items-end gap-2">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" checked={currentStep?.use_ai_personalization || false}
                        onChange={e => updateStep({ use_ai_personalization: e.target.checked })}
                        className="accent-purple-600" />
                      <span className="text-sm flex items-center gap-1"><Sparkles className="w-3.5 h-3.5 text-purple-600" /> Personnalisation IA</span>
                    </label>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">Objet</label>
                  <input value={currentStep?.subject_template || ''}
                    onChange={e => updateStep({ subject_template: e.target.value })}
                    className="w-full px-3 py-2 text-sm border rounded font-mono" />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">Corps (HTML ou texte)</label>
                  <textarea value={currentStep?.body_template || ''}
                    onChange={e => updateStep({ body_template: e.target.value })}
                    rows={8} className="w-full px-3 py-2 text-sm border rounded font-mono text-xs resize-none" />
                </div>
                {currentStep?.use_ai_personalization && (
                  <div>
                    <label className="block text-xs font-medium mb-1 text-purple-700">Instruction IA (comment personnaliser)</label>
                    <textarea value={currentStep?.ai_personalization_prompt || ''}
                      onChange={e => updateStep({ ai_personalization_prompt: e.target.value })}
                      rows={2} placeholder="Ex: Mentionne le secteur d'activité et adapte le ton au profil de l'entreprise"
                      className="w-full px-3 py-2 text-sm border border-purple-200 rounded bg-purple-50 resize-none" />
                  </div>
                )}
              </div>
            </div>
            <div className="px-6 py-4 border-t flex justify-end gap-2">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 border rounded text-sm">Annuler</button>
              <button onClick={() => createMutation.mutate(form)}
                disabled={!form.name || createMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded text-sm disabled:opacity-50">
                Créer la séquence
              </button>
            </div>
          </div>
        )}

        {/* Liste des séquences */}
        {isLoading && <p className="text-gray-500 text-sm">Chargement…</p>}
        {!isLoading && (!sequences || sequences.length === 0) && (
          <EmptyState title="Aucune séquence" description="Créez votre première séquence d'emails automatisés."
            icon={<Mail className="w-12 h-12" />} />
        )}
        {sequences?.map((seq) => (
          <div key={seq.id} className="bg-white rounded-lg border p-4 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${seq.is_active ? 'bg-green-500' : 'bg-gray-300'}`} />
                <span className="font-medium">{seq.name}</span>
                {seq.is_active
                  ? <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">Active</span>
                  : <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">Pausée</span>
                }
              </div>
              {seq.description && <p className="text-sm text-gray-500 mt-0.5">{seq.description}</p>}
            </div>
            <div className="flex items-center gap-2">
              {seq.is_active && (
                <button onClick={() => pauseMutation.mutate(seq.id)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs border rounded hover:bg-gray-50">
                  <Pause className="w-3.5 h-3.5" /> Pausé
                </button>
              )}
              <button onClick={() => deleteMutation.mutate(seq.id)}
                className="p-1.5 text-gray-400 hover:text-red-500">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
