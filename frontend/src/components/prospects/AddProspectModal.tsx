import { useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { useCreateProspect, useCreateProspectBySiret } from '../../hooks/useProspects';
import { cn } from '../../lib/utils';

interface AddProspectModalProps {
  open: boolean;
  onClose: () => void;
}

type Tab = 'siret' | 'manual';

export function AddProspectModal({ open, onClose }: AddProspectModalProps) {
  const [tab, setTab] = useState<Tab>('siret');
  const [identifier, setIdentifier] = useState('');
  const [manualForm, setManualForm] = useState({
    company_name: '',
    siren: '',
    city: '',
    postal_code: '',
    phone: '',
    email: '',
    website: '',
    notes: '',
  });

  const createBySiret = useCreateProspectBySiret();
  const createManual = useCreateProspect();

  if (!open) return null;

  const isLoading = createBySiret.isPending || createManual.isPending;

  const submitSiret = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleaned = identifier.replace(/\s/g, '');
    if (!/^\d{9}$|^\d{14}$/.test(cleaned)) return;
    try {
      await createBySiret.mutateAsync(cleaned);
      setIdentifier('');
      onClose();
    } catch {
      // toast déjà géré
    }
  };

  const submitManual = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualForm.company_name.trim()) return;
    try {
      await createManual.mutateAsync({
        company_name: manualForm.company_name.trim(),
        siren: manualForm.siren || null,
        city: manualForm.city || null,
        postal_code: manualForm.postal_code || null,
        phone: manualForm.phone || null,
        email: manualForm.email || null,
        website: manualForm.website || null,
        notes: manualForm.notes || null,
      });
      setManualForm({
        company_name: '', siren: '', city: '', postal_code: '',
        phone: '', email: '', website: '', notes: '',
      });
      onClose();
    } catch {
      // toast déjà géré
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-bold">Ajouter un prospect</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded" disabled={isLoading}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <TabButton active={tab === 'siret'} onClick={() => setTab('siret')}>
            🔍 Par SIREN / SIRET
          </TabButton>
          <TabButton active={tab === 'manual'} onClick={() => setTab('manual')}>
            ✍️ Saisie manuelle
          </TabButton>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {tab === 'siret' && (
            <form onSubmit={submitSiret} className="space-y-4">
              <p className="text-sm text-gray-600">
                Entrez un SIREN (9 chiffres) ou SIRET (14 chiffres). Les données seront récupérées
                automatiquement depuis l'INSEE, BODACC, Pappers, Pages Jaunes et Google Maps.
              </p>
              <div>
                <label className="block text-sm font-medium mb-1">SIREN ou SIRET *</label>
                <input
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="Ex: 552120222 ou 55212022200016"
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isLoading}
                  required
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button type="button" onClick={onClose} className="px-4 py-2 border rounded hover:bg-gray-50" disabled={isLoading}>
                  Annuler
                </button>
                <button type="submit" disabled={isLoading || !identifier} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
                  {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                  {isLoading ? 'Enrichissement…' : 'Créer le prospect'}
                </button>
              </div>
            </form>
          )}

          {tab === 'manual' && (
            <form onSubmit={submitManual} className="space-y-4">
              <Field label="Nom de l'entreprise *" required>
                <input
                  type="text"
                  value={manualForm.company_name}
                  onChange={(e) => setManualForm({ ...manualForm, company_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  required
                  disabled={isLoading}
                />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="SIREN">
                  <input type="text" value={manualForm.siren} onChange={(e) => setManualForm({ ...manualForm, siren: e.target.value })} className="w-full px-3 py-2 border rounded" disabled={isLoading} />
                </Field>
                <Field label="Téléphone">
                  <input type="tel" value={manualForm.phone} onChange={(e) => setManualForm({ ...manualForm, phone: e.target.value })} className="w-full px-3 py-2 border rounded" disabled={isLoading} />
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Ville">
                  <input type="text" value={manualForm.city} onChange={(e) => setManualForm({ ...manualForm, city: e.target.value })} className="w-full px-3 py-2 border rounded" disabled={isLoading} />
                </Field>
                <Field label="Code postal">
                  <input type="text" value={manualForm.postal_code} onChange={(e) => setManualForm({ ...manualForm, postal_code: e.target.value })} className="w-full px-3 py-2 border rounded" disabled={isLoading} />
                </Field>
              </div>
              <Field label="Email">
                <input type="email" value={manualForm.email} onChange={(e) => setManualForm({ ...manualForm, email: e.target.value })} className="w-full px-3 py-2 border rounded" disabled={isLoading} />
              </Field>
              <Field label="Site web">
                <input type="url" value={manualForm.website} onChange={(e) => setManualForm({ ...manualForm, website: e.target.value })} className="w-full px-3 py-2 border rounded" disabled={isLoading} />
              </Field>
              <Field label="Notes">
                <textarea value={manualForm.notes} onChange={(e) => setManualForm({ ...manualForm, notes: e.target.value })} className="w-full px-3 py-2 border rounded" rows={3} disabled={isLoading} />
              </Field>

              <div className="flex gap-2 pt-2">
                <button type="button" onClick={onClose} className="px-4 py-2 border rounded hover:bg-gray-50" disabled={isLoading}>
                  Annuler
                </button>
                <button type="submit" disabled={isLoading || !manualForm.company_name} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
                  {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                  Créer le prospect
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'px-6 py-3 text-sm font-medium border-b-2 transition',
        active ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-600 hover:text-gray-900',
      )}
    >
      {children}
    </button>
  );
}

function Field({ label, children, required }: { label: string; children: React.ReactNode; required?: boolean }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </label>
      {children}
    </div>
  );
}
