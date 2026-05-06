import { useDroppable } from '@dnd-kit/core';
import type { KanbanColumn as KanbanColumnType } from '../../types';
import { ProspectCard } from './ProspectCard';

interface KanbanColumnProps {
  column: KanbanColumnType;
}

export function KanbanColumn({ column }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: column.stage.id,
    data: { type: 'column', stage: column.stage },
  });

  return (
    <div
      ref={setNodeRef}
      className={`flex flex-col bg-gray-50 rounded-lg p-3 min-w-[280px] w-[280px] flex-shrink-0 transition ${
        isOver ? 'ring-2 ring-blue-400 bg-blue-50' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <span
            className="w-3 h-3 rounded-full inline-block"
            style={{ backgroundColor: column.stage.color }}
          />
          <h3 className="font-semibold text-sm">{column.stage.name}</h3>
        </div>
        <span className="text-xs px-2 py-0.5 bg-white rounded-full font-medium text-gray-600">
          {column.count}
        </span>
      </div>

      <div className="space-y-2 overflow-y-auto flex-1 min-h-[200px]">
        {column.cards.map((card) => (
          <ProspectCard key={card.id} card={card} />
        ))}
        {column.cards.length === 0 && (
          <div className="flex items-center justify-center h-32 text-xs text-gray-400 border border-dashed border-gray-300 rounded">
            Glisser une carte ici
          </div>
        )}
      </div>
    </div>
  );
}
