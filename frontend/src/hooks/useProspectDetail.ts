import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { auditService, painPointService, pipelineService } from '@/services';

interface Interaction {
  id: string;
  type: 'call' | 'email' | 'linkedin' | 'whatsapp' | 'note' | 'meeting';
  content: string;
  date: string;
  userId: string;
}

export function useProspectDetail(prospectId: string) {
  const [prospect, setProspect] = useState<any>(null);
  const [audit, setAudit] = useState<any>(null);
  const [painPoints, setPainPoints] = useState<any[]>([]);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'audit' | 'angles' | 'interactions'>('overview');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch prospect details, audit, pain points, and interactions
        // For now using mock data - replace with actual API calls
        setProspect({
          id: prospectId,
          raisonSociale: 'Entreprise Example',
          siren: '123456789',
          siret: '12345678900012',
          adresse: '123 Rue de la République, 75001 Paris',
          codeNaf: '6201Z',
          effectifs: 50,
          ca: 2500000,
          siteWeb: 'https://example.com',
          email: 'contact@example.com',
          telephone: '01 23 45 67 89',
          stage: 'nouveau',
          scoreDigital: 65,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        });

        setInteractions([
          {
            id: '1',
            type: 'email',
            content: 'Premier contact par email envoyé',
            date: new Date(Date.now() - 86400000 * 2).toISOString(),
            userId: 'user1',
          },
          {
            id: '2',
            type: 'call',
            content: 'Appel de découverte - intérêt pour nos solutions',
            date: new Date(Date.now() - 86400000).toISOString(),
            userId: 'user1',
          },
        ]);
      } catch (error) {
        console.error('Error fetching data:', error);
        toast.error('Erreur lors du chargement des données');
      } finally {
        setLoading(false);
      }
    };

    if (prospectId) {
      fetchData();
    }
  }, [prospectId]);

  const handleLaunchAudit = async () => {
    try {
      const result = await auditService.launchDigital(prospectId);
      setAudit(result);
      setActiveTab('audit');
      toast.success('Audit digital lancé avec succès');
    } catch (error) {
      toast.error('Erreur lors du lancement de l\'audit');
    }
  };

  const handleGenerateAngles = async () => {
    try {
      const angles = await painPointService.generateAngles(prospectId);
      setPainPoints(angles);
      setActiveTab('angles');
      toast.success('Angles commerciaux générés');
    } catch (error) {
      toast.error('Erreur lors de la génération des angles');
    }
  };

  const handleAddInteraction = async (type: Interaction['type'], content: string) => {
    try {
      await pipelineService.addInteraction(prospectId, type, content);
      const newInteraction: Interaction = {
        id: Date.now().toString(),
        type,
        content,
        date: new Date().toISOString(),
        userId: 'current-user',
      };
      setInteractions([newInteraction, ...interactions]);
      toast.success('Interaction ajoutée');
    } catch (error) {
      toast.error('Erreur lors de l\'ajout de l\'interaction');
    }
  };

  const handleChangeStage = async (stage: string) => {
    try {
      await pipelineService.changeStage(prospectId, stage);
      setProspect((prev: any) => ({ ...prev, stage }));
      toast.success('Étape mise à jour');
    } catch (error) {
      toast.error('Erreur lors de la mise à jour de l\'étape');
    }
  };

  return {
    prospect,
    audit,
    painPoints,
    interactions,
    loading,
    activeTab,
    setActiveTab,
    handleLaunchAudit,
    handleGenerateAngles,
    handleAddInteraction,
    handleChangeStage,
  };
}
