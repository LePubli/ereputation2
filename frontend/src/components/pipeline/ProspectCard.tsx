import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import type { KanbanCard } from '../../types';
import { formatCurrency, getPropensityColor } from '../../lib/utils';

interface ProspectCardProps {
  card: KanbanCard;
}

export function ProspectCard({ card }: ProspectCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: card.id,
    data: { type: 'card', card },
  });

  const style: React.CSSProperties = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
    cursor: isDragging ? 'grabbing' : 'grab',
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className="bg-white rounded-md border border-gray-200 p-3 shadow-sm hover:shadow-md transition select-none"
    >
      <div className="flex items-start justify-between mb-2">
        <h4 className="text-sm font-semibold text-gray-900 line-clamp-2">{card.company_name}</h4>
        {card.propensity_category && (
          <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded border ${getPropensityColor(card.propensity_category)}`}>
            {card.propensity_category}
          </span>
        )}
      </div>
      <div className="space-y-1 text-xs text-gray-500">
        {card.city && <div className="flex items-center gap-1">📍 {card.city}</div>}
        {card.estimated_revenue != null && (
          <div className="flex items-center gap-1 text-gray-700 font-medium">
            💰 {formatCurrency(card.estimated_revenue)}
          </div>
        )}
        {card.tags && card.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {card.tags.slice(0, 3).map((t) => (
              <span key={t} className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
