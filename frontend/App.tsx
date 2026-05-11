import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import AppShell from './components/layout/AppShell';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProspectsPage from './pages/ProspectsPage';
import PipelinePage from './pages/PipelinePage';
import TableView from './pages/TableView';
import AIAgentPage from './pages/AIAgentPage';
import SignalsPage from './pages/SignalsPage';
import SequencerPage from './pages/SequencerPage';
import InboundPage from './pages/InboundPage';
import ContactIntelPage from './pages/ContactIntelPage';
import WebhooksPage from './pages/WebhooksPage';
import SettingsPage from './pages/SettingsPage';
import PluginsPage from './pages/PluginsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SourcingPage from './pages/SourcingPage';
import ABMPage from './pages/ABMPage';
import CRMSyncPage from './pages/CRMSyncPage';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg-primary)' }}><div style={{ width: '20px', height: '20px', border: '2px solid var(--border-color)', borderTopColor: 'var(--accent-blue)', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} /><style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style></div>;
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><AppShell /></PrivateRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="prospects" element={<ProspectsPage />} />
          <Route path="pipeline" element={<PipelinePage />} />
          <Route path="table" element={<TableView />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="sourcing" element={<SourcingPage />} />
          <Route path="signals" element={<SignalsPage />} />
          <Route path="sequencer" element={<SequencerPage />} />
          <Route path="inbound" element={<InboundPage />} />
          <Route path="contacts" element={<ContactIntelPage />} />
          <Route path="agent" element={<AIAgentPage />} />
          <Route path="abm" element={<ABMPage />} />
          <Route path="crm-sync" element={<CRMSyncPage />} />
          <Route path="webhooks" element={<WebhooksPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="plugins" element={<PluginsPage />} />
        </Route>
        <Route path="*" element={<div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg-primary)', flexDirection: 'column', gap: '1rem' }}><div style={{ fontSize: '4rem', fontWeight: 700, color: 'var(--text-muted)' }}>404</div><a href="/" style={{ color: 'var(--accent-blue)' }}>← Retour</a></div>} />
      </Routes>
    </BrowserRouter>
  );
}
