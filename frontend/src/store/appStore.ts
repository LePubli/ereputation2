import { create } from 'zustand';
import type { Prospect, Plugin, Metrics } from '@/types';

interface AppState {
  // Prospects
  prospects: Prospect[];
  selectedProspect: Prospect | null;
  loading: boolean;
  error: string | null;

  // Plugins
  plugins: Plugin[];
  activePlugins: string[];

  // Métriques
  metrics: Metrics | null;

  // Actions
  setProspects: (prospects: Prospect[]) => void;
  setSelectedProspect: (prospect: Prospect | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setPlugins: (plugins: Plugin[]) => void;
  setActivePlugins: (plugins: string[]) => void;
  setMetrics: (metrics: Metrics | null) => void;
  addProspect: (prospect: Prospect) => void;
  updateProspect: (id: string, updates: Partial<Prospect>) => void;
  removeProspect: (id: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // État initial
  prospects: [],
  selectedProspect: null,
  loading: false,
  error: null,
  plugins: [],
  activePlugins: [],
  metrics: null,

  // Actions
  setProspects: (prospects) => set({ prospects }),
  setSelectedProspect: (prospect) => set({ selectedProspect: prospect }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setPlugins: (plugins) => set({ plugins, activePlugins: plugins.filter(p => p.active).map(p => p.name) }),
  setActivePlugins: (activePlugins) => set({ activePlugins }),
  setMetrics: (metrics) => set({ metrics }),
  
  addProspect: (prospect) => set((state) => ({
    prospects: [...state.prospects, prospect]
  })),
  
  updateProspect: (id, updates) => set((state) => ({
    prospects: state.prospects.map(p => 
      p.id === id ? { ...p, ...updates } : p
    ),
    selectedProspect: state.selectedProspect?.id === id 
      ? { ...state.selectedProspect, ...updates } 
      : state.selectedProspect
  })),
  
  removeProspect: (id) => set((state) => ({
    prospects: state.prospects.filter(p => p.id !== id),
    selectedProspect: state.selectedProspect?.id === id ? null : state.selectedProspect
  })),
}));
