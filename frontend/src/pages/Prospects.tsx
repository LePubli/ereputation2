import { useState } from 'react';
import { FileUpload } from '@/components/FileUpload';
import { useProspects } from '@/hooks';
import { prospectService } from '@/services';
import toast from 'react-hot-toast';

export default function Prospects() {
  const { prospects, loading, refresh, search } = useProspects();
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [siretInput, setSiretInput] = useState('');

  const handleSearch = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    if (query.length >= 3) {
      await search(query);
    } else if (query.length === 0) {
      await refresh();
    }
  };

  const handleAddBySiret = async () => {
    if (!siretInput.trim()) {
      toast.error('Veuillez entrer un SIRET');
      return;
    }

    try {
      await prospectService.createBySiret(siretInput.trim());
      toast.success('Prospect ajouté avec succès');
      setShowAddModal(false);
      setSiretInput('');
      await refresh();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout du prospect');
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Prospects</h1>
          <p className="text-gray-500 mt-1">Gérez votre base de prospects</p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="btn-primary">
          <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Ajouter un prospect
        </button>
      </div>

      {/* Search and Import */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Rechercher un prospect..."
                value={searchQuery}
                onChange={handleSearch}
                className="input-field"
              />
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
            Import en masse
          </h3>
          <FileUpload onImportComplete={refresh} />
        </div>
      </div>

      {/* Prospects List */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entreprise
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SIREN
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score Digital
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Étape
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {prospects.map((prospect: any) => (
                <tr key={prospect.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {prospect.raisonSociale}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {prospect.siren}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {prospect.scoreDigital !== undefined ? (
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2 w-24">
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
                        <span className="text-xs">{prospect.scoreDigital}%</span>
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      prospect.stage === 'gagne' ? 'bg-green-100 text-green-700' :
                      prospect.stage === 'perdu' ? 'bg-red-100 text-red-700' :
                      prospect.stage === 'negociation' ? 'bg-purple-100 text-purple-700' :
                      prospect.stage === 'rdv_pris' ? 'bg-orange-100 text-orange-700' :
                      prospect.stage === 'contacte' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {prospect.stage}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <a href={`/prospects/${prospect.id}`} className="text-primary-600 hover:text-primary-900">
                      Voir
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="card w-full max-w-md mx-4">
            <h2 className="text-xl font-bold mb-4">Ajouter un prospect</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Par SIRET
                </label>
                <input
                  type="text"
                  placeholder="Entrez le SIRET (14 chiffres)"
                  value={siretInput}
                  onChange={(e) => setSiretInput(e.target.value)}
                  className="input-field"
                  maxLength={14}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button onClick={handleAddBySiret} className="btn-primary flex-1">
                  Ajouter
                </button>
                <button onClick={() => setShowAddModal(false)} className="btn-secondary flex-1">
                  Annuler
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
