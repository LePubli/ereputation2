import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { auditService, painPointService } from '@/services';

export default function ProspectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [prospect, setProspect] = useState<any>(null);
  const [audit, setAudit] = useState<any>(null);
  const [painPoints, setPainPoints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'audit' | 'angles'>('overview');

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Dans une implémentation complète, on fetcherait les détails du prospect
        // Pour l'instant, on utilise des données mockées
        setProspect({
          id,
          raisonSociale: 'Entreprise Example',
          siren: '123456789',
          stage: 'nouveau',
        });
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleLaunchAudit = async () => {
    try {
      const result = await auditService.launchDigital(id!);
      setAudit(result);
      setActiveTab('audit');
    } catch (error) {
      console.error('Error launching audit:', error);
    }
  };

  const handleGenerateAngles = async () => {
    try {
      const angles = await painPointService.generateAngles(id!);
      setPainPoints(angles);
      setActiveTab('angles');
    } catch (error) {
      console.error('Error generating angles:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate('/prospects')}
            className="text-sm text-gray-500 hover:text-gray-700 mb-2"
          >
            ← Retour aux prospects
          </button>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {prospect?.raisonSociale}
          </h1>
          <p className="text-gray-500">SIREN: {prospect?.siren}</p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleLaunchAudit} className="btn-secondary">
            Lancer un audit digital
          </button>
          <button onClick={handleGenerateAngles} className="btn-primary">
            Générer des angles
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex gap-6">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Vue d'ensemble
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'audit'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Audit Digital
          </button>
          <button
            onClick={() => setActiveTab('angles')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'angles'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Angles Commerciaux
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Informations générales</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm text-gray-500">Raison sociale</label>
              <p className="font-medium">{prospect?.raisonSociale}</p>
            </div>
            <div>
              <label className="block text-sm text-gray-500">SIREN</label>
              <p className="font-medium">{prospect?.siren}</p>
            </div>
            <div>
              <label className="block text-sm text-gray-500">Étape actuelle</label>
              <p className="font-medium capitalize">{prospect?.stage}</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="space-y-6">
          {audit ? (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Résultats de l'audit</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <p className="text-sm text-gray-500">Score global</p>
                  <p className="text-3xl font-bold text-primary-600">{audit.overallScore}/100</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 card">
              <p className="text-gray-500 mb-4">Aucun audit réalisé pour ce prospect</p>
              <button onClick={handleLaunchAudit} className="btn-primary">
                Lancer un audit digital
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'angles' && (
        <div className="space-y-6">
          {painPoints.length > 0 ? (
            painPoints.map((point) => (
              <div key={point.id} className="card">
                <div className="flex items-start justify-between mb-3">
                  <h4 className="font-semibold text-lg">{point.category}</h4>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    point.severity === 'critical' ? 'bg-red-100 text-red-700' :
                    point.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                    point.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {point.severity}
                  </span>
                </div>
                <p className="text-gray-700 dark:text-gray-300 mb-3">{point.description}</p>
                <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded-lg">
                  <p className="text-sm font-medium text-gray-500 mb-1">Action recommandée</p>
                  <p className="text-gray-900 dark:text-white">{point.recommendedAction}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12 card">
              <p className="text-gray-500 mb-4">Aucun angle commercial généré</p>
              <button onClick={handleGenerateAngles} className="btn-primary">
                Générer des angles commerciaux
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
