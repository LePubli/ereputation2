// API prospects
import { apiClient } from './client';
import type {
  Prospect,
  ProspectImportResult,
  ProspectListResponse,
} from '../types';

export interface ProspectListParams {
  page?: number;
  page_size?: number;
  search?: string;
  stage_id?: string;
}

export interface ProspectCreatePayload {
  company_name: string;
  siren?: string | null;
  siret?: string | null;
  city?: string | null;
  postal_code?: string | null;
  address?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  notes?: string | null;
  tags?: string[];
  stage_id?: string | null;
}

export interface ProspectUpdatePayload extends Partial<ProspectCreatePayload> {
  consent_given?: boolean;
  opt_out?: boolean;
}

export const prospectsApi = {
  list: async (params: ProspectListParams = {}): Promise<ProspectListResponse> => {
    const { data } = await apiClient.get<ProspectListResponse>('/prospects', { params });
    return data;
  },

  get: async (id: string): Promise<Prospect> => {
    const { data } = await apiClient.get<Prospect>(`/prospects/${id}`);
    return data;
  },

  createManual: async (payload: ProspectCreatePayload): Promise<Prospect> => {
    const { data } = await apiClient.post<Prospect>('/prospects', payload);
    return data;
  },

  createBySiret: async (identifier: string): Promise<Prospect> => {
    const { data } = await apiClient.post<Prospect>('/prospects/by-siret', { identifier });
    return data;
  },

  update: async (id: string, payload: ProspectUpdatePayload): Promise<Prospect> => {
    const { data } = await apiClient.patch<Prospect>(`/prospects/${id}`, payload);
    return data;
  },

  updateStage: async (id: string, stage_id: string, position = 0): Promise<Prospect> => {
    const { data } = await apiClient.patch<Prospect>(`/prospects/${id}/stage`, {
      stage_id,
      position,
    });
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/prospects/${id}`);
  },

  reenrich: async (id: string): Promise<Prospect> => {
    const { data } = await apiClient.post<Prospect>(`/prospects/${id}/enrich`);
    return data;
  },

  importFile: async (file: File): Promise<ProspectImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await apiClient.post<ProspectImportResult>('/prospects/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
};
