import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import { prospectService } from '@/services';

interface FileUploadProps {
  onImportComplete?: (result: { imported: number; failed: number }) => void;
}

export function FileUpload({ onImportComplete }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    
    // Vérifier le type de fichier
    const validTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];

    if (!validTypes.includes(file.type) && !file.name.endsWith('.csv')) {
      toast.error('Format de fichier non supporté. Veuillez utiliser CSV ou Excel.');
      return;
    }

    try {
      setUploading(true);
      const result = await prospectService.importFromFile(file);
      toast.success(`${result.imported} prospects importés avec succès`);
      if (result.failed > 0) {
        // toast.warning n'existe pas dans react-hot-toast → on utilise l'API générique
        toast(`${result.failed} échecs lors de l'import`, {
          icon: '⚠️',
          style: {
            background: '#FEF3C7',
            color: '#92400E',
          },
        });
      }
      onImportComplete?.(result);
    } catch (error) {
      toast.error('Erreur lors de l\'import du fichier');
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    multiple: false,
    disabled: uploading
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
        ${isDragActive 
          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' 
          : 'border-gray-300 dark:border-gray-600 hover:border-primary-400'
        }`}
    >
      <input {...getInputProps()} />
      
      {uploading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          <p className="text-gray-600 dark:text-gray-400">Import en cours...</p>
        </div>
      ) : isDragActive ? (
        <div className="flex flex-col items-center gap-3">
          <svg className="w-12 h-12 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="text-primary-600 font-medium">Déposez le fichier ici</p>
          <p className="text-sm text-gray-500">CSV ou Excel</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <div>
            <p className="text-gray-700 dark:text-gray-300 font-medium">
              Glissez-déposez un fichier ou cliquez pour parcourir
            </p>
            <p className="text-sm text-gray-500 mt-1">CSV, XLS ou XLSX (max 10MB)</p>
          </div>
        </div>
      )}
    </div>
  );
}
