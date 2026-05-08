import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { useSystemInfo } from '../hooks/usePlugins';
import { PageHeader } from '../components/layout/AppShell';
import { Skeleton } from '../components/ui/Skeleton';

export default function Settings() {
  const { data, isLoading, error } = useSystemInfo();

  return (
    <>
      <PageHeader title="Paramètres" description="Configuration système et état des services" />

      <div className="p-6 space-y-6">
        {/* État du système */}
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">État du système</h2>

          {isLoading && (
            <div className="space-y-2">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-6 w-48" />
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 text-red-600">
              <XCircle className="w-5 h-5" />
              <span>Backend non joignable</span>
            </div>
          )}

          {data && (
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
              <Row label="Application" value={`${data.app_name} v${data.app_version}`} />
              <Row label="Statut global" value={<StatusBadge status={data.status} />} />
              <Row label="Base de données" value={<StatusBadge status={data.database === 'ok' ? 'healthy' : 'unhealthy'} customLabel={data.database} />} />
              <Row label="Redis" value={<StatusBadge status={data.redis === 'ok' ? 'healthy' : 'unhealthy'} customLabel={data.redis} />} />
              <Row label="Plugins enregistrés" value={`${data.plugins_count} (${data.plugins_active.length} actifs)`} />
              <Row label="Uptime" value={formatUptime(data.uptime_seconds)} />
            </dl>
          )}
        </section>

        {/* Plugins actifs */}
        {data && data.plugins_active.length > 0 && (
          <section className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-3">Plugins actifs</h2>
            <div className="flex flex-wrap gap-2">
              {data.plugins_active.map((p) => (
                <span key={p} className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded text-sm font-medium">
                  {p}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Sources de scraping */}
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-3">Sources de données B2B</h2>
          <p className="text-sm text-gray-500 mb-4">
            Sources publiques utilisées pour l'enrichissement (aucune clé API requise) :
          </p>
          <ul className="space-y-2 text-sm">
            <SourceRow name="INSEE / Sirene" url="https://recherche-entreprises.api.gouv.fr" type="API publique data.gouv.fr" />
            <SourceRow name="BODACC" url="https://bodacc-datadila.opendatasoft.com" type="API publique data.gouv.fr" />
            <SourceRow name="Pappers" url="https://www.pappers.fr" type="Scraping HTTP (rate-limited 2s)" />
            <SourceRow name="Pages Jaunes" url="https://www.pagesjaunes.fr" type="Scraping HTTP (rate-limited 3s)" />
            <SourceRow name="Google Maps" url="https://www.google.com/maps" type="Scraping Playwright (headless)" />
          </ul>
        </section>

        {/* Documentation API */}
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-3">Documentation API</h2>
          <div className="flex flex-wrap gap-3">
            <a href="/docs" target="_blank" rel="noreferrer noopener" className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50">
              📘 Swagger UI
            </a>
            <a href="/redoc" target="_blank" rel="noreferrer noopener" className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50">
              📕 ReDoc
            </a>
            <a href="/openapi.json" target="_blank" rel="noreferrer noopener" className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50">
              📄 OpenAPI JSON
            </a>
          </div>
        </section>
      </div>
    </>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <dt className="text-sm text-gray-500">{label}</dt>
      <dd className="text-sm font-medium text-gray-900">{value}</dd>
    </div>
  );
}

function StatusBadge({ status, customLabel }: { status: string; customLabel?: string }) {
  if (status === 'healthy') {
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs"><CheckCircle2 className="w-3.5 h-3.5" /> {customLabel ?? 'Sain'}</span>;
  }
  if (status === 'degraded') {
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs"><AlertTriangle className="w-3.5 h-3.5" /> Dégradé</span>;
  }
  return <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs"><XCircle className="w-3.5 h-3.5" /> {customLabel ?? 'Erreur'}</span>;
}

function SourceRow({ name, url, type }: { name: string; url: string; type: string }) {
  return (
    <li className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <div>
        <span className="font-medium">{name}</span>
        <span className="text-xs text-gray-500 ml-2">({type})</span>
      </div>
      <a href={url} target="_blank" rel="noreferrer noopener" className="text-xs text-blue-600 hover:underline">
        {url}
      </a>
    </li>
  );
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}j ${h}h ${m}min`;
  if (h > 0) return `${h}h ${m}min`;
  return `${m}min`;
}
