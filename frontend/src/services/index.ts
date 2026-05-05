import apiClient from './api';
import type { Prospect, DigitalAudit, PainPoint, Plugin, Metrics } from '@/types';

export const prospectService = {
  // Créer un prospect par SIRET
  createBySiret: async (siret: string): Promise<Prospect> => {
    const response = await apiClient.post('/prospects', { siret });
    return response.data;
  },

  // Récupérer un prospect par SIREN
  getBySiren: async (siren: string): Promise<Prospect> => {
    const response = await apiClient.get(`/prospects/${siren}`);
    return response.data;
  },

  // Rechercher des prospects
  search: async (query: string): Promise<Prospect[]> => {
    const response = await apiClient.get(`/prospects/search?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  // Lister tous les prospects
  list: async (): Promise<Prospect[]> => {
    const response = await apiClient.get('/prospects');
    return response.data;
  },

  // Mettre à jour le stage d'un prospect
  updateStage: async (prospectId: string, stage: string): Promise<Prospect> => {
    const response = await apiClient.patch(`/pipeline/${prospectId}/stage`, { stage });
    return response.data;
  },

  // Importer des prospects depuis un fichier CSV/Excel
  importFromFile: async (file: File): Promise<{ imported: number; failed: number }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/prospects/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

export const auditService = {
  // Lancer un audit digital
  launchDigital: async (prospectId: string): Promise<DigitalAudit> => {
    const response = await apiClient.post(`/audit/digital/${prospectId}`);
    return response.data;
  },

  // Récupérer les résultats d'un audit
  getDigital: async (prospectId: string): Promise<DigitalAudit> => {
    const response = await apiClient.get(`/audit/digital/${prospectId}`);
    return response.data;
  },

  // Récupérer le score digital
  getDigitalScore: async (prospectId: string): Promise<{ score: number }> => {
    const response = await apiClient.get(`/audit/digital/${prospectId}/score`);
    return response.data;
  },
};

export const painPointService = {
  // Générer des angles commerciaux
  generateAngles: async (prospectId: string): Promise<PainPoint[]> => {
    const response = await apiClient.post('/angles/generate', { prospectId });
    return response.data;
  },

  // Récupérer les angles d'un prospect
  getByProspect: async (prospectId: string): Promise<PainPoint[]> => {
    const response = await apiClient.get(`/angles/${prospectId}`);
    return response.data;
  },

  // Reformuler un angle avec LLM
  formatAngle: async (angleId: string, tone: string): Promise<PainPoint> => {
    const response = await apiClient.post(`/angles/${angleId}/format`, { tone });
    return response.data;
  },
};

export const pipelineService = {
  // Récupérer la vue Kanban complète
  getPipeline: async () => {
    const response = await apiClient.get('/pipeline');
    return response.data;
  },

  // Changer l'étape d'un prospect
  changeStage: async (prospectId: string, stage: string): Promise<void> => {
    await apiClient.patch(`/pipeline/${prospectId}/stage`, { stage });
  },

  // Récupérer les métriques
  getMetrics: async (): Promise<Metrics> => {
    const response = await apiClient.get('/pipeline/metrics');
    return response.data;
  },

  // Ajouter une interaction
  addInteraction: async (prospectId: string, type: string, content: string): Promise<void> => {
    await apiClient.post(`/pipeline/${prospectId}/interactions`, { type, content });
  },

  // Récupérer les alertes
  getAlerts: async () => {
    const response = await apiClient.get('/pipeline/alerts');
    return response.data;
  },
};

export const pluginService = {
  // Lister tous les plugins
  list: async (): Promise<Plugin[]> => {
    const response = await apiClient.get('/plugins');
    return response.data.plugins;
  },

  // Activer un plugin
  enable: async (pluginName: string): Promise<void> => {
    await apiClient.post(`/plugins/${pluginName}/enable`);
  },

  // Désactiver un plugin
  disable: async (pluginName: string): Promise<void> => {
    await apiClient.post(`/plugins/${pluginName}/disable`);
  },

  // Installer un plugin depuis un fichier ZIP
  installFromZip: async (file: File): Promise<{ success: boolean; pluginName: string }> => {
    const formData = new FormData();
    formData.append('plugin', file);
    const response = await apiClient.post('/plugins/install', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Mettre à jour un plugin
  update: async (pluginName: string): Promise<void> => {
    await apiClient.post(`/plugins/${pluginName}/update`);
  },

  // Désinstaller un plugin
  uninstall: async (pluginName: string): Promise<void> => {
    await apiClient.delete(`/plugins/${pluginName}`);
  },
};

export const systemService = {
  // Vérifier la santé de l'application
  healthCheck: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Vérifier la readiness
  readinessCheck: async () => {
    const response = await apiClient.get('/ready');
    return response.data;
  },

  // Mettre à jour l'application
  updateApp: async (): Promise<{ success: boolean; version: string }> => {
    const response = await apiClient.post('/system/update');
    return response.data;
  },

  // Récupérer la version actuelle
  getVersion: async (): Promise<{ version: string }> => {
    const response = await apiClient.get('/');
    return response.data;
  },
};
