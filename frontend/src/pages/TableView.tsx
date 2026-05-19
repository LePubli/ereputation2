import { PageHeader } from '../components/ui/PageHeader';

import { SpreadsheetView } from '../components/spreadsheet/SpreadsheetView';

export default function TableView() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <SpreadsheetView />
    </div>
  );
}
}
