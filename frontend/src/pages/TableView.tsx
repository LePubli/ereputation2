import { SpreadsheetView } from '../components/spreadsheet/SpreadsheetView';
import { PageHeader } from '../components/ui/PageHeader';

export default function TableView() {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <PageHeader
        title="Spreadsheet"
        description="Vue tabulaire Clay-style — colonnes dynamiques, AI Agent, enrichissement multi-sources"
      />
      <div className="flex-1 overflow-hidden">
        <SpreadsheetView />
      </div>
    </div>
  );
}
