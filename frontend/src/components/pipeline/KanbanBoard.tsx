import { useState } from 'react';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core';
import { usePipelineBoard, useMoveProspect } from '../../hooks/usePipeline';
import type { KanbanCard } from '../../types';
import { KanbanColumn } from './KanbanColumn';
import { ProspectCard } from './ProspectCard';
import { Skeleton } from '../ui/Skeleton';
import { EmptyState } from '../ui/EmptyState';
import { Workflow } from 'lucide-react';

export function KanbanBoard() {
  const { data, isLoading, error } = usePipelineBoard();
  const moveProspect = useMoveProspect();
  const [activeCard, setActiveCard] = useState<KanbanCard | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  );

  const handleDragStart = (event: DragStartEvent) => {
    const card = event.active.data.current?.card as KanbanCard | undefined;
    if (card) setActiveCard(card);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveCard(null);
    const { active, over } = event;
    if (!over) return;

    const card = active.data.current?.card as KanbanCard | undefined;
    const newStageId = over.id as string;
    if (!card || !newStageId) return;

    // Si la carte est dans la même colonne, ne rien faire
    const currentColumn = data?.columns.find((col) => col.cards.some((c) => c.id === card.id));
    if (currentColumn?.stage.id === newStageId) return;

    await moveProspect.mutateAsync({
      id: card.id,
      stage_id: newStageId,
      position: 0,
    });
  };

  if (isLoading) {
    return (
      <div className="flex gap-4 overflow-x-auto p-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-50 rounded-lg p-3 min-w-[280px] w-[280px]">
            <Skeleton className="h-6 w-32 mb-3" />
            <div className="space-y-2">
              <Skeleton className="h-20" />
              <Skeleton className="h-20" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        title="Impossible de charger le pipeline"
        description="Vérifiez la connexion au backend."
        icon={<Workflow className="w-12 h-12" />}
      />
    );
  }

  if (!data || data.columns.length === 0) {
    return (
      <EmptyState
        title="Aucune étape de pipeline configurée"
        description="Le seed initial n'a pas été exécuté ou les étapes ont été supprimées."
        icon={<Workflow className="w-12 h-12" />}
      />
    );
  }

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="flex gap-4 overflow-x-auto p-4 min-h-[calc(100vh-200px)]">
        {data.columns.map((column) => (
          <KanbanColumn key={column.stage.id} column={column} />
        ))}
      </div>
      <DragOverlay>
        {activeCard ? (
          <div className="rotate-3">
            <ProspectCard card={activeCard} />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
