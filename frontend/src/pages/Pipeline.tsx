import { useState } from 'react';
import { KanbanColumn } from '@/components/KanbanBoard';
import { usePipeline } from '@/hooks';

const stages = [
  { id: 'nouveau', label: 'Nouveau', color: 'bg-blue-500' },
  { id: 'contacte', label: 'Contacté', color: 'bg-yellow-500' },
  { id: 'rdv_pris', label: 'RDV pris', color: 'bg-orange-500' },
  { id: 'negociation', label: 'En négociation', color: 'bg-purple-500' },
  { id: 'gagne', label: 'Gagné', color: 'bg-green-500' },
  { id: 'perdu', label: 'Perdu', color: 'bg-red-500' },
];

export default function Pipeline() {
  const { pipeline, loading, error, refresh, changeStage } = usePipeline();
  const [draggedId, setDraggedId] = useState<string | null>(null);

  const handleDragStart = (id: string) => {
    setDraggedId(id);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (stageId: string) => {
    if (draggedId) {
      try {
        await changeStage(draggedId, stageId);
        await refresh();
      } catch (error) {
        console.error('Error changing stage:', error);
      } finally {
        setDraggedId(null);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <button onClick={refresh} className="btn-primary mt-4">
          Réessayer
        </button>
      </div>
    );
  }

  const prospectsByStage = pipeline?.prospects || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Pipeline Kanban</h1>
          <p className="text-gray-500 mt-1">Glissez-déposez les prospects entre les étapes</p>
        </div>
        <button onClick={refresh} className="btn-secondary">
          Actualiser
        </button>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4">
        {stages.map((stage) => (
          <KanbanColumn
            key={stage.id}
            stage={stage}
            prospects={prospectsByStage.filter((p: any) => p.stage === stage.id)}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragStart={handleDragStart}
          />
        ))}
      </div>
    </div>
  );
}
