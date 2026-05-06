import { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { pipelineService } from '@/services';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

interface AnalyticsData {
  dailyConversions: Array<{ date: string; count: number }>;
  stageEvolution: Array<{ date: string; [key: string]: number }>;
  performanceBySource: Array<{ source: string; count: number; conversionRate: number }>;
  avgTimeInStage: Array<{ stage: string; days: number }>;
}

export default function Analytics() {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        // Données mockées pour la démo - à remplacer par un appel API réel
        const mockData: AnalyticsData = {
          dailyConversions: [
            { date: '01/05', count: 3 },
            { date: '02/05', count: 5 },
            { date: '03/05', count: 2 },
            { date: '04/05', count: 8 },
            { date: '05/05', count: 6 },
            { date: '06/05', count: 4 },
            { date: '07/05', count: 7 },
          ],
          stageEvolution: [
            { date: '01/05', nouveau: 12, contacte: 8, rdv_pris: 5, negociation: 3, gagne: 2 },
            { date: '02/05', nouveau: 14, contacte: 9, rdv_pris: 6, negociation: 4, gagne: 3 },
            { date: '03/05', nouveau: 11, contacte: 10, rdv_pris: 7, negociation: 5, gagne: 3 },
            { date: '04/05', nouveau: 15, contacte: 12, rdv_pris: 8, negociation: 6, gagne: 4 },
            { date: '05/05', nouveau: 13, contacte: 11, rdv_pris: 9, negociation: 7, gagne: 5 },
            { date: '06/05', nouveau: 16, contacte: 13, rdv_pris: 10, negociation: 8, gagne: 6 },
            { date: '07/05', nouveau: 14, contacte: 14, rdv_pris: 11, negociation: 9, gagne: 7 },
          ],
          performanceBySource: [
            { source: 'Import CSV', count: 45, conversionRate: 0.22 },
            { source: 'SIRET Manuel', count: 30, conversionRate: 0.35 },
            { source: 'API INSEE', count: 25, conversionRate: 0.28 },
          ],
          avgTimeInStage: [
            { stage: 'Nouveau', days: 2.5 },
            { stage: 'Contacté', days: 4.2 },
            { stage: 'RDV pris', days: 7.8 },
            { stage: 'Négociation', days: 12.3 },
            { stage: 'Gagné', days: 0 },
          ],
        };
        setAnalytics(mockData);
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [timeRange]);

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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analytics</h1>
          <p className="text-gray-500 mt-1">Tableaux de bord et indicateurs de performance</p>
        </div>
        
        <div className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-lg p-1 shadow-sm">
          {(['7d', '30d', '90d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                timeRange === range
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              {range === '7d' ? '7 jours' : range === '30d' ? '30 jours' : '90 jours'}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Conversions (période)</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">35</p>
              <p className="text-sm text-green-600 mt-1">↑ 12% vs période précédente</p>
            </div>
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Taux de conversion</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">28.5%</p>
              <p className="text-sm text-green-600 mt-1">↑ 3.2% vs période précédente</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Temps moyen cycle</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">18j</p>
              <p className="text-sm text-red-600 mt-1">↓ 2j vs période précédente</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Prospects actifs</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">124</p>
              <p className="text-sm text-green-600 mt-1">↑ 18 nouveaux cette semaine</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Conversions */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Conversions quotidiennes
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={analytics?.dailyConversions}>
              <defs>
                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="date" className="text-xs" />
              <YAxis className="text-xs" />
              <RechartsTooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                  border: 'none',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Area type="monotone" dataKey="count" stroke="#3B82F6" fillOpacity={1} fill="url(#colorCount)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Avg Time in Stage */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Temps moyen par étape (jours)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics?.avgTimeInStage}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="stage" className="text-xs" />
              <YAxis className="text-xs" />
              <RechartsTooltip
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                  border: 'none',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Bar dataKey="days" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stage Evolution */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Évolution du pipeline
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analytics?.stageEvolution}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="date" className="text-xs" />
              <YAxis className="text-xs" />
              <RechartsTooltip
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                  border: 'none',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="nouveau" stroke="#3B82F6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="contacte" stroke="#EAB308" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="rdv_pris" stroke="#F97316" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="negociation" stroke="#A855F7" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="gagne" stroke="#22C55E" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Performance by Source */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Performance par source
          </h3>
          <div className="space-y-4">
            {analytics?.performanceBySource.map((item) => (
              <div key={item.source} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{item.source}</span>
                  <span className="text-sm text-gray-500">{item.count} prospects</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                    <div
                      className="bg-primary-500 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${(item.count / 50) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-primary-600 w-16 text-right">
                    {(item.conversionRate * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Insights Section */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          💡 Insights & Recommandations
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
            <p className="text-sm font-medium text-green-800 dark:text-green-300 mb-1">🎯 Taux de conversion excellent</p>
            <p className="text-xs text-green-600 dark:text-green-400">Votre taux de conversion de 28.5% est supérieur à la moyenne du secteur (22%). Continuez ainsi !</p>
          </div>
          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300 mb-1">⏱️ Optimisation possible</p>
            <p className="text-xs text-yellow-600 dark:text-yellow-400">La phase de négociation prend en moyenne 12 jours. Envisagez d'automatiser le suivi.</p>
          </div>
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <p className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-1">📈 Source performante</p>
            <p className="text-xs text-blue-600 dark:text-blue-400">Les ajouts manuels par SIRET ont le meilleur taux de conversion (35%). Privilégiez cette méthode.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
