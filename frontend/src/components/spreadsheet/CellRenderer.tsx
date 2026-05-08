import { ExternalLink, Sparkles, Phone } from 'lucide-react';
import type { Prospect, ColumnConfig } from '../../types';
import { getPropensityColor } from '../../lib/utils';

interface CellRendererProps {
  prospect: Prospect;
  column: ColumnConfig;
  onAgentClick?: (p: Prospect) => void;
}

/** Extrait la valeur d'un prospect en suivant le field_path (ex: "enrichment.rating") */
function extractValue(prospect: Prospect, field_path: string): any {
  const parts = field_path.split('.');
  let val: any = prospect;
  for (const part of parts) {
    if (val == null) return null;
    val = val[part as keyof typeof val];
  }
  return val;
}

export function CellRenderer({ prospect, column, onAgentClick }: CellRendererProps) {
  // Valeur depuis ai_enrichment en priorité si source = ai_agent
  let value: any;
  if (column.source === 'ai_agent') {
    const aiData = (prospect as any).ai_enrichment?.[column.field_path];
    value = aiData?.value ?? null;
  } else {
    value = extractValue(prospect, column.field_path);
  }

  // Status de l'enrichissement
  const status = getEnrichmentStatus(prospect, column);

  switch (column.display_type) {
    case 'text':
      return <TextCell value={value} status={status} />;
    case 'mono':
      return <MonoCell value={value} />;
    case 'phone':
      return <PhoneCell value={value} status={status} />;
    case 'url':
      return <UrlCell value={value} status={status} />;
    case 'email':
      return <EmailCell value={value} status={status} />;
    case 'score':
      return <ScoreCell value={value} />;
    case 'category':
      return <CategoryCell value={value} />;
    case 'badge':
      return <BadgeCell value={value} status={status} />;
    case 'sources':
      return <SourcesCell value={value} />;
    case 'boolean':
      return <BoolCell value={value} />;
    case 'ai':
      return <AiCell value={value} prospect={prospect} column={column} onClick={onAgentClick} />;
    default:
      return <TextCell value={value} status={status} />;
  }
}

function getEnrichmentStatus(prospect: Prospect, col: ColumnConfig): 'enriched' | 'empty' | 'pending' {
  const sources = prospect.sources_used || [];
  if (col.source === 'core') return 'enriched';
  if (col.source === 'ai_agent') {
    const ai = (prospect as any).ai_enrichment?.[col.field_path];
    return ai?.value != null ? 'enriched' : 'empty';
  }
  return sources.includes(col.source) ? 'enriched' : 'empty';
}

function StatusDot({ status }: { status: string }) {
  const cls = status === 'enriched' ? 'dot dot-green'
    : status === 'pending' ? 'dot dot-blue animate-pulse-dot'
    : 'dot dot-gray';
  return <span className={cls} />;
}

function TextCell({ value, status }: { value: any; status: string }) {
  if (!value) return <div className="flex items-center gap-1.5 text-gray-300 text-xs"><StatusDot status={status} />—</div>;
  return (
    <div className="flex items-center gap-1.5">
      <StatusDot status="enriched" />
      <span className="truncate text-xs">{String(value)}</span>
    </div>
  );
}

function MonoCell({ value }: { value: any }) {
  if (!value) return <span className="text-gray-300 text-xs">—</span>;
  return <span className="font-mono text-xs text-gray-700">{value}</span>;
}

function PhoneCell({ value, status }: { value: any; status: string }) {
  if (!value) return <div className="flex items-center gap-1 text-gray-300 text-xs"><StatusDot status={status} />—</div>;
  return (
    <a href={`tel:${value}`} onClick={(e) => e.stopPropagation()}
      className="flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs">
      <Phone className="w-3 h-3" />
      {value}
    </a>
  );
}

function UrlCell({ value, status }: { value: any; status: string }) {
  if (!value) return <div className="flex items-center gap-1 text-gray-300 text-xs"><StatusDot status={status} />—</div>;
  const display = value.replace(/^https?:\/\//, '').replace(/\/$/, '');
  return (
    <a href={value} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}
      className="flex items-center gap-1 text-blue-600 hover:underline text-xs truncate max-w-full">
      <ExternalLink className="w-3 h-3 flex-shrink-0" />
      <span className="truncate">{display}</span>
    </a>
  );
}

function EmailCell({ value, status }: { value: any; status: string }) {
  if (!value) return <div className="flex items-center gap-1 text-gray-300 text-xs"><StatusDot status={status} />—</div>;
  return (
    <a href={`mailto:${value}`} onClick={(e) => e.stopPropagation()}
      className="text-blue-600 hover:underline text-xs truncate block">
      {value}
    </a>
  );
}

function ScoreCell({ value }: { value: any }) {
  if (value == null) return <span className="text-gray-300 text-xs">—</span>;
  const score = Math.round(Number(value));
  const color = score >= 70 ? '#16a34a' : score >= 40 ? '#ea580c' : '#6b7280';
  return (
    <div className="flex items-center gap-1.5">
      <div className="relative w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div className="absolute inset-y-0 left-0 rounded-full"
          style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="text-xs font-medium" style={{ color }}>{score}</span>
    </div>
  );
}

function CategoryCell({ value }: { value: any }) {
  if (!value) return <span className="text-gray-300 text-xs">—</span>;
  const cls = value === 'HOT' ? 'bg-red-100 text-red-700'
    : value === 'WARM' ? 'bg-orange-100 text-orange-700'
    : 'bg-gray-100 text-gray-600';
  return (
    <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded ${cls}`}>{value}</span>
  );
}

function BadgeCell({ value, status }: { value: any; status: string }) {
  if (!value) return <div className="flex items-center gap-1 text-gray-300 text-xs"><StatusDot status={status} />—</div>;
  return (
    <div className="flex items-center gap-1">
      <StatusDot status="enriched" />
      <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-700 rounded truncate">{String(value)}</span>
    </div>
  );
}

function SourcesCell({ value }: { value: any }) {
  if (!value || !Array.isArray(value) || value.length === 0) {
    return <span className="text-gray-300 text-xs">—</span>;
  }
  const sourceColors: Record<string, string> = {
    insee: 'source-insee', bodacc: 'source-bodacc', pappers: 'source-pappers',
    pages_jaunes: 'source-pages_jaunes', google_maps: 'source-google_maps',
    ai_agent: 'source-ai_agent', societe_com: 'source-societe_com',
    trustpilot: 'source-trustpilot',
  };
  return (
    <div className="flex gap-1 items-center overflow-hidden">
      {(value as string[]).slice(0, 4).map((s) => (
        <span key={s} className={`source-badge ${sourceColors[s] || ''}`}>{s.split('_')[0]}</span>
      ))}
      {value.length > 4 && <span className="text-xs text-gray-400">+{value.length - 4}</span>}
    </div>
  );
}

function BoolCell({ value }: { value: any }) {
  return value
    ? <span className="text-green-600 text-xs font-medium">✓ Oui</span>
    : <span className="text-gray-400 text-xs">Non</span>;
}

function AiCell({ value, prospect, column, onClick }: {
  value: any; prospect: Prospect; column: ColumnConfig;
  onClick?: (p: Prospect) => void;
}) {
  if (value != null) {
    return (
      <div className="flex items-center gap-1.5 group">
        <span className="w-2 h-2 rounded-full bg-purple-500 flex-shrink-0" />
        <span className="text-xs truncate">{String(value)}</span>
        <button onClick={(e) => { e.stopPropagation(); onClick?.(prospect); }}
          className="opacity-0 group-hover:opacity-100 p-0.5 text-purple-500 hover:text-purple-700">
          <Sparkles className="w-3 h-3" />
        </button>
      </div>
    );
  }
  return (
    <button
      onClick={(e) => { e.stopPropagation(); onClick?.(prospect); }}
      className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-700 hover:bg-purple-50 px-1.5 py-0.5 rounded transition"
    >
      <Sparkles className="w-3 h-3" /> Générer
    </button>
  );
}
