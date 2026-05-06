// Client axios centralisé avec interception des erreurs et toast
import axios, { AxiosError } from 'axios';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    // Pas de spam de toast pour les annulations user
    if (axios.isCancel(error)) {
      return Promise.reject(error);
    }

    const status = error.response?.status;
    const detail = error.response?.data?.detail;

    if (status === 401 || status === 403) {
      toast.error("Authentification requise", {
        description: 'Veuillez vous reconnecter.',
      });
    } else if (status === 404) {
      // Le composant gère lui-même l'affichage du 404
    } else if (status === 422) {
      toast.error('Données invalides', {
        description: typeof detail === 'string' ? detail : 'Vérifiez le formulaire.',
      });
    } else if (status === 502) {
      toast.error('Source externe indisponible', {
        description: typeof detail === 'string' ? detail : "Réessayez dans quelques instants.",
      });
    } else if (status && status >= 500) {
      toast.error('Erreur serveur', {
        description: typeof detail === 'string' ? detail : "Le serveur a rencontré une erreur.",
      });
    } else if (!status) {
      toast.error('Connexion impossible', {
        description: "Vérifiez votre connexion internet.",
      });
    }

    return Promise.reject(error);
  },
);
