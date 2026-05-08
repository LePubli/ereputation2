import { PageHeader } from '../components/layout/AppShell';
import { KanbanBoard } from '../components/pipeline/KanbanBoard';
import { usePipelineBoard } from '../hooks/usePipeline';

export default function Pipeline() {
  const { data } = usePipelineBoard();

  return (
    <>
      <PageHeader
        title="Pipeline commercial"
        description={
          data
            ? `${data.total} prospect(s) répartis sur ${data.columns.length} étape(s) — Glissez-déposez pour changer d'étape`
            : 'Pipeline commercial — Glissez-déposez pour changer d\'étape'
        }
      />
      <KanbanBoard />
    </>
  );
}
