import { X, ExternalLink, RefreshCw, Phone, Mail, Globe, MapPin, Building2, Calendar, Users, TrendingUp } from 'lucide-react';
import type { Prospect } from '../../types';
import { ActivityTimeline } from './ActivityTimeline';
import { useReenrichProspect } from '../../hooks/useProspects';
import { formatCurrency, formatDate, getPropensityColor } from '../../lib/utils';

interface ProspectDrawerProps {
  prospect: Prospect | null;
  onClose: () => void;
}

export function ProspectDrawer({ prospect, onClose }: ProspectDrawerProps) {
  const reenrich = useReenrichProspect();

  if (!prospect) return null;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/30 z-40" onClick={onClose} />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-full max-w-2xl bg-white shadow-2xl z-50 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between px-6 py-4 border-b bg-gray-50 flex-shrink-0">
          <div>
            <h2 className="text-lg font-bold text-gray-900 leading-tight">{prospect.company_name}</h2>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              {prospect.siren && <span className="text-xs text-gray-500 font-mono">SIREN {prospect.siren}</span>}
              {prospect.naf_label && <span className="text-xs text-gray-500">· {prospect.naf_label}</span>}
              {prospect.propensity_category && (
                <span className={`text-xs px-2 py-0.5 rounded border font-medium ${getPropensityColor(prospect.propensity_category)}`}>
                  {prospect.propensity_category} {prospect.propensity_score ? `(${Math.round(prospect.propensity_score)})` : ''}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => reenrich.mutate(prospect.id)}
              disabled={reenrich.isPending}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs border rounded hover:bg-gray-100 disabled:opacity-50"
              title="Ré-enrichir depuis les sources"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${reenrich.isPending ? 'animate-spin' : ''}`} />
              Ré-enrichir
            </button>
            <button onClick={onClose} className="p-1.5 hover:bg-gray-200 rounded">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body scrollable */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Coordonnées */}
          <Section title="Coordonnées">
            <div className="grid grid-cols-2 gap-3">
              <InfoRow icon={<Phone />} label="Téléphone" value={prospect.phone}
                href={prospect.phone ? `tel:${prospect.phone}` : undefined} />
              <InfoRow icon={<Mail />} label="Email" value={prospect.email}
                href={prospect.email ? `mailto:${prospect.email}` : undefined} />
              <InfoRow icon={<Globe />} label="Site web" value={prospect.website}
                href={prospect.website || undefined} external />
              <InfoRow icon={<MapPin />} label="Adresse"
                value={[prospect.address, prospect.city, prospect.postal_code].filter(Boolean).join(', ')} />
            </div>
          </Section>

          {/* Informations légales */}
          <Section title="Informations légales">
            <div className="grid grid-cols-2 gap-3">
              <InfoRow icon={<Building2 />} label="Forme juridique" value={prospect.legal_form} />
              <InfoRow icon={<Calendar />} label="Création" value={formatDate(prospect.creation_date)} />
              <InfoRow icon={<Users />} label="Effectifs" value={prospect.employee_range} />
              <InfoRow icon={<TrendingUp />} label="CA estimé" value={formatCurrency(prospect.estimated_revenue)} />
            </div>
          </Section>

          {/* Scoring détaillé */}
          {prospect.scoring_details && Object.keys(prospect.scoring_details).length > 0 && (
            <Section title="Scoring détaillé">
              <div className="bg-gray-50 rounded-lg p-3 space-y-2">
                {[
                  { key: 'web_presence', label: 'Présence web', max: 25 },
                  { key: 'employee_range', label: 'Effectifs', max: 22 },
                  { key: 'google_rating', label: 'Avis Google', max: 15 },
                  { key: 'company_age', label: 'Ancienneté', max: 15 },
                  { key: 'bodacc_signals', label: 'Signaux BODACC', max: 13 },
                  { key: 'completeness', label: 'Complétude', max: 10 },
                ].map(({ key, label, max }) => {
                  const val = (prospect.scoring_details as any)[key] ?? 0;
                  const pct = Math.round((val / max) * 100);
                  return (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-600">{label}</span>
                        <span className="font-medium">{val}/{max}</span>
                      </div>
                      <div className="h-1.5 bg-gray-200 rounded-full">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </Section>
          )}

          {/* Contacts (dirigeants) */}
          {prospect.contacts && prospect.contacts.length > 0 && (
            <Section title="Contacts">
              <div className="space-y-2">
                {prospect.contacts.map((c) => (
                  <div key={c.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div>
                      <div className="text-sm font-medium">{[c.first_name, c.last_name].filter(Boolean).join(' ') || '—'}</div>
                      {c.role && <div className="text-xs text-gray-500">{c.role}</div>}
                    </div>
                    <div className="flex gap-2">
                      {c.phone && <a href={`tel:${c.phone}`} className="text-xs text-blue-600 hover:underline">{c.phone}</a>}
                      {c.email && <a href={`mailto:${c.email}`} className="text-xs text-blue-600 hover:underline">{c.email}</a>}
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Sources */}
          <Section title="Sources de données">
            <div className="flex flex-wrap gap-1.5">
              {prospect.sources_used.map((s) => (
                <span key={s} className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded border border-blue-200">{s}</span>
              ))}
              {prospect.last_enriched_at && (
                <span className="text-xs text-gray-400 ml-2">Dernière MàJ: {formatDate(prospect.last_enriched_at)}</span>
              )}
            </div>
          </Section>

          {/* Timeline activités */}
          <Section title="">
            <ActivityTimeline prospect_id={prospect.id} />
          </Section>
        </div>
      </div>
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      {title && <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">{title}</h3>}
      {children}
    </div>
  );
}

function InfoRow({ icon, label, value, href, external }: {
  icon: React.ReactNode; label: string; value: string | null | undefined;
  href?: string; external?: boolean;
}) {
  const content = value || '—';
  return (
    <div className="flex items-start gap-2">
      <div className="text-gray-400 mt-0.5 w-4 flex-shrink-0">{icon}</div>
      <div className="min-w-0">
        <div className="text-xs text-gray-500">{label}</div>
        {href && value ? (
          <a href={href} target={external ? '_blank' : undefined} rel="noreferrer"
            className="text-sm text-blue-600 hover:underline flex items-center gap-1 truncate">
            <span className="truncate">{content}</span>
            {external && <ExternalLink className="w-3 h-3 flex-shrink-0" />}
          </a>
        ) : (
          <div className="text-sm text-gray-900 truncate">{content}</div>
        )}
      </div>
    </div>
  );
}
