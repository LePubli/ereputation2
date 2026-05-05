import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

export const stages = [
  { id: 'nouveau', label: 'Nouveau', color: 'bg-blue-500' },
  { id: 'contacte', label: 'Contacté', color: 'bg-yellow-500' },
  { id: 'rdv_pris', label: 'RDV pris', color: 'bg-orange-500' },
  { id: 'negociation', label: 'En négociation', color: 'bg-purple-500' },
  { id: 'gagne', label: 'Gagné', color: 'bg-green-500' },
  { id: 'perdu', label: 'Perdu', color: 'bg-red-500' },
];

interface ProspectCardProps {
  prospect: {
    id: string;
    raisonSociale: string;
    siren: string;
    scoreDigital?: number;
    stage: string;
  };
  onDragStart: (id: string) => void;
}

export function ProspectCard({ prospect, onDragStart }: ProspectCardProps) {
  const navigate = useNavigate();

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      draggable
      onDragStart={() => onDragStart(prospect.id)}
      onClick={() => navigate(`/prospects/${prospect.id}`)}
      className="card cursor-pointer hover:shadow-lg transition-shadow mb-3"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 dark:text-white">
            {prospect.raisonSociale}
          </h4>
          <p className="text-sm text-gray-500">SIREN: {prospect.siren}</p>
          {prospect.scoreDigital !== undefined && (
            <div className="mt-2">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Score digital:</span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      prospect.scoreDigital >= 70
                        ? 'bg-green-500'
                        : prospect.scoreDigital >= 40
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${prospect.scoreDigital}%` }}
                  />
                </div>
                <span className="text-xs font-medium">{prospect.scoreDigital}%</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

interface KanbanColumnProps {
  stage: {
    id: string;
    label: string;
    color: string;
  };
  prospects: Array<{
    id: string;
    raisonSociale: string;
    siren: string;
    scoreDigital?: number;
    stage: string;
  }>;
  onDrop: (stageId: string) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragStart: (id: string) => void;
}

export function KanbanColumn({ stage, prospects, onDrop, onDragOver, onDragStart }: KanbanColumnProps) {
  return (
    <div
      className="flex-1 min-w-[280px] bg-gray-100 dark:bg-gray-900 rounded-lg p-4"
      onDrop={() => onDrop(stage.id)}
      onDragOver={onDragOver}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${stage.color}`} />
          <h3 className="font-semibold text-gray-900 dark:text-white">{stage.label}</h3>
        </div>
        <span className="bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium px-2.5 py-0.5 rounded-full">
          {prospects.length}
        </span>
      </div>

      <div className="space-y-2">
        {prospects.map((prospect) => (
          <ProspectCard
            key={prospect.id}
            prospect={prospect}
            onDragStart={onDragStart}
          />
        ))}
      </div>
    </div>
  );
}
