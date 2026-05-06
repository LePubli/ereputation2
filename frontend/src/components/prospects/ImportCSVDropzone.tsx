import { useRef, useState } from 'react';
import { Upload, FileSpreadsheet } from 'lucide-react';
import { useImportProspects } from '../../hooks/useProspects';
import { Spinner } from '../ui/Spinner';

export function ImportCSVDropzone() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const importMutation = useImportProspects();

  const handleFile = async (file: File) => {
    if (!/\.(csv|xls|xlsx)$/i.test(file.name)) {
      alert('Format non supporté (CSV, XLS, XLSX)');
      return;
    }
    await importMutation.mutateAsync(file);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
      className={`flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-lg cursor-pointer transition ${
        dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
      }`}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xls,.xlsx"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = '';
        }}
      />
      {importMutation.isPending ? (
        <Spinner label="Import en cours…" />
      ) : (
        <>
          <FileSpreadsheet className="w-10 h-10 text-gray-400 mb-2" />
          <p className="text-sm font-medium">Glissez un fichier CSV / XLSX ici</p>
          <p className="text-xs text-gray-500 mt-1">ou cliquez pour parcourir</p>
          <p className="text-xs text-gray-400 mt-2">
            Colonnes attendues : company_name, siren, city, postal_code, email, phone, website
          </p>
        </>
      )}
    </div>
  );
}
