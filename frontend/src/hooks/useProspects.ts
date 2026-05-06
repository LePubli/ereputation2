import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { prospectsApi, type ProspectCreatePayload, type ProspectListParams, type ProspectUpdatePayload } from '../api/prospects';

export const useProspects = (params: ProspectListParams = {}) =>
  useQuery({
    queryKey: ['prospects', params],
    queryFn: () => prospectsApi.list(params),
    staleTime: 30_000,
  });

export const useProspect = (id: string | undefined) =>
  useQuery({
    queryKey: ['prospect', id],
    queryFn: () => prospectsApi.get(id!),
    enabled: !!id,
  });

export const useCreateProspect = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProspectCreatePayload) => prospectsApi.createManual(payload),
    onSuccess: () => {
      toast.success('Prospect créé');
      qc.invalidateQueries({ queryKey: ['prospects'] });
      qc.invalidateQueries({ queryKey: ['pipeline-board'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
};

export const useCreateProspectBySiret = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (identifier: string) => prospectsApi.createBySiret(identifier),
    onSuccess: () => {
      toast.success('Prospect enrichi avec succès');
      qc.invalidateQueries({ queryKey: ['prospects'] });
      qc.invalidateQueries({ queryKey: ['pipeline-board'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
};

export const useUpdateProspect = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ProspectUpdatePayload }) =>
      prospectsApi.update(id, payload),
    onSuccess: (_, vars) => {
      toast.success('Prospect mis à jour');
      qc.invalidateQueries({ queryKey: ['prospects'] });
      qc.invalidateQueries({ queryKey: ['prospect', vars.id] });
    },
  });
};

export const useDeleteProspect = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => prospectsApi.delete(id),
    onSuccess: () => {
      toast.success('Prospect supprimé');
      qc.invalidateQueries({ queryKey: ['prospects'] });
      qc.invalidateQueries({ queryKey: ['pipeline-board'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
};

export const useReenrichProspect = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => prospectsApi.reenrich(id),
    onSuccess: (_, id) => {
      toast.success('Données réactualisées');
      qc.invalidateQueries({ queryKey: ['prospect', id] });
      qc.invalidateQueries({ queryKey: ['prospects'] });
    },
  });
};

export const useImportProspects = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => prospectsApi.importFile(file),
    onSuccess: (data) => {
      toast.success(
        `${data.imported} prospect(s) importé(s)`,
        { description: data.skipped > 0 ? `${data.skipped} ignoré(s)` : undefined },
      );
      qc.invalidateQueries({ queryKey: ['prospects'] });
      qc.invalidateQueries({ queryKey: ['pipeline-board'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
};
