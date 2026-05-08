import { Trash2, RefreshCw, ExternalLink } from 'lucide-react';
import type { Prospect } from '../../types';
import { useDeleteProspect, useReenrichProspect } from '../../hooks/useProspects';
import { formatCurrency, formatDate, getPropensityColor } from '../../lib/utils';

interface ProspectsTableProps {
  prospects: Prospect[];
  onRowClick?: (p: Prospect) => void;
}

export function ProspectsTable({ prospects, onRowClick }: ProspectsTableProps) {
  const deleteMutation = useDeleteProspect();
  const reenrichMutation = useReenrichProspect();

  return (
    <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b">
          <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <th className="px-4 py-3">Entreprise</th>
            <th className="px-4 py-3">Ville</th>
            <th className="px-4 py-3">Tél.</th>
            <th className="px-4 py-3">Score</th>
            <th className="px-4 py-3">CA estimé</th>
            <th className="px-4 py-3">Activités</th>
            <th className="px-4 py-3">Créé</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {prospects.map((p) => (
            <tr
              key={p.id}
              className="hover:bg-blue-50 transition cursor-pointer"
              onClick={() => onRowClick?.(p)}
            >
              <td className="px-4 py-3">
                <div className="font-medium text-gray-900">{p.company_name}</div>
                {p.naf_label && <div className="text-xs text-gray-500 truncate max-w-xs">{p.naf_label}</div>}
              </td>
              <td className="px-4 py-3 text-gray-600">{p.city ?? '—'}</td>
              <td className="px-4 py-3 text-gray-600">{p.phone ?? '—'}</td>
              <td className="px-4 py-3">
                {p.propensity_category ? (
                  <span className={`px-2 py-0.5 text-xs font-medium rounded border ${getPropensityColor(p.propensity_category)}`}>
                    {p.propensity_category} {p.propensity_score ? `${Math.round(p.propensity_score)}` : ''}
                  </span>
                ) : '—'}
              </td>
              <td className="px-4 py-3 font-medium">{formatCurrency(p.estimated_revenue)}</td>
              <td className="px-4 py-3">
                {p.activities_count > 0
                  ? <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">{p.activities_count}</span>
                  : <span className="text-xs text-gray-400">0</span>
                }
              </td>
              <td className="px-4 py-3 text-gray-500">{formatDate(p.created_at)}</td>
              <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                <div className="inline-flex items-center gap-1">
                  {p.website && (
                    <a href={p.website} target="_blank" rel="noreferrer noopener"
                      className="p-1.5 text-gray-400 hover:text-blue-600">
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                  <button onClick={() => reenrichMutation.mutate(p.id)}
                    disabled={reenrichMutation.isPending}
                    className="p-1.5 text-gray-400 hover:text-blue-600 disabled:opacity-50">
                    <RefreshCw className={`w-4 h-4 ${reenrichMutation.isPending && reenrichMutation.variables === p.id ? 'animate-spin' : ''}`} />
                  </button>
                  <button onClick={() => { if (confirm(`Supprimer ${p.company_name} ?`)) deleteMutation.mutate(p.id); }}
                    className="p-1.5 text-gray-400 hover:text-red-600">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
