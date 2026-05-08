import { useState } from 'react';
import { Phone, Mail, Users, FileText, CheckSquare, Linkedin, MoreHorizontal, Trash2, Plus } from 'lucide-react';
import { useActivities, useCreateActivity, useDeleteActivity } from '../../hooks/useActivities';
import { Spinner } from '../ui/Spinner';
import type { ActivityType, ActivityOutcome } from '../../types';

const TYPE_CONFIG: Record<ActivityType, { icon: React.ReactNode; label: string; color: string }> = {
  call:     { icon: <Phone className="w-4 h-4" />,     label: 'Appel',      color: 'bg-blue-100 text-blue-700' },
  email:    { icon: <Mail className="w-4 h-4" />,      label: 'Email',      color: 'bg-purple-100 text-purple-700' },
  meeting:  { icon: <Users className="w-4 h-4" />,     label: 'RDV',        color: 'bg-green-100 text-green-700' },
  note:     { icon: <FileText className="w-4 h-4" />,  label: 'Note',       color: 'bg-gray-100 text-gray-700' },
  task:     { icon: <CheckSquare className="w-4 h-4" />,label: 'Tâche',     color: 'bg-orange-100 text-orange-700' },
  linkedin: { icon: <Linkedin className="w-4 h-4" />,  label: 'LinkedIn',   color: 'bg-sky-100 text-sky-700' },
  other:    { icon: <MoreHorizontal className="w-4 h-4" />, label: 'Autre', color: 'bg-gray-100 text-gray-600' },
};

const OUTCOME_BADGE: Record<ActivityOutcome, string> = {
  positive: 'bg-green-100 text-green-700',
  neutral:  'bg-gray-100 text-gray-600',
  negative: 'bg-red-100 text-red-700',
};

export function ActivityTimeline({ prospect_id }: { prospect_id: string }) {
  const { data: activities, isLoading } = useActivities(prospect_id);
  const createMutation = useCreateActivity();
  const deleteMutation = useDeleteActivity();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ type: 'call' as ActivityType, title: '', body: '', outcome: '' as ActivityOutcome | '' });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    await createMutation.mutateAsync({
      prospect_id,
      type: form.type,
      title: form.title.trim(),
      body: form.body || undefined,
      outcome: form.outcome || undefined,
    });
    setForm({ type: 'call', title: '', body: '', outcome: '' });
    setShowForm(false);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Activités commerciales</h3>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-1 px-2.5 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Plus className="w-3 h-3" />
          Ajouter
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 rounded-lg p-3 space-y-2 border">
          <div className="grid grid-cols-2 gap-2">
            <select
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value as ActivityType })}
              className="px-2 py-1.5 text-sm border rounded"
            >
              {Object.entries(TYPE_CONFIG).map(([k, v]) => (
                <option key={k} value={k}>{v.label}</option>
              ))}
            </select>
            <select
              value={form.outcome}
              onChange={(e) => setForm({ ...form, outcome: e.target.value as ActivityOutcome })}
              className="px-2 py-1.5 text-sm border rounded"
            >
              <option value="">Résultat…</option>
              <option value="positive">✅ Positif</option>
              <option value="neutral">➖ Neutre</option>
              <option value="negative">❌ Négatif</option>
            </select>
          </div>
          <input
            type="text"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="Titre de l'activité *"
            className="w-full px-2 py-1.5 text-sm border rounded"
            required
          />
          <textarea
            value={form.body}
            onChange={(e) => setForm({ ...form, body: e.target.value })}
            placeholder="Notes…"
            rows={2}
            className="w-full px-2 py-1.5 text-sm border rounded resize-none"
          />
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setShowForm(false)} className="px-3 py-1 text-sm border rounded">
              Annuler
            </button>
            <button type="submit" disabled={createMutation.isPending} className="px-3 py-1 text-sm bg-blue-600 text-white rounded disabled:opacity-50">
              Ajouter
            </button>
          </div>
        </form>
      )}

      {isLoading && <Spinner label="Chargement…" />}

      {!isLoading && (!activities || activities.length === 0) && (
        <p className="text-sm text-gray-400 py-4 text-center">Aucune activité enregistrée</p>
      )}

      <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
        {activities?.map((activity) => {
          const cfg = TYPE_CONFIG[activity.type] || TYPE_CONFIG.other;
          return (
            <div key={activity.id} className="flex gap-3 group">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${cfg.color}`}>
                {cfg.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-sm font-medium text-gray-900">{activity.title}</span>
                    {activity.outcome && (
                      <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${OUTCOME_BADGE[activity.outcome]}`}>
                        {activity.outcome}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => deleteMutation.mutate({ id: activity.id, prospect_id })}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                {activity.body && <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{activity.body}</p>}
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(activity.created_at).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
