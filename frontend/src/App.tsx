import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import AppShell from './components/layout/AppShell';

// Pages
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
import ThemesPage from './pages/ThemesPage';
import { ThemeProvider } from './components/ThemeProvider';
// Lazy stubs for pages not yet fully built
import { lazy, Suspense } from 'react';

const ABMPage = lazy(() => import('./pages/ABMPage').catch(() => ({ default: StubPage('🎯 ABM / TAM Sourcing', 'Ciblage de comptes stratégiques et analyse du marché total adressable') })));
const CRMSyncPage = lazy(() => import('./pages/CRMSyncPage').catch(() => ({ default: StubPage('🔄 CRM Sync', 'Synchronisation bidirectionnelle avec HubSpot') })));

function StubPage(title: string, desc: string) {
  return function Page() {
    return (
      <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: '1rem' }}>
        <div style={{ fontSize: '3rem' }}>{title.split(' ')[0]}</div>
        <h2 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '1.25rem' }}>{title.slice(2)}</h2>
        <p style={{ color: 'var(--text-muted)', textAlign: 'center', maxWidth: '400px' }}>{desc}</p>
        <div style={{
          padding: '0.625rem 1.25rem', borderRadius: '8px',
          background: 'rgba(47,129,247,0.1)', border: '1px solid rgba(47,129,247,0.3)',
          color: 'var(--accent-blue)', fontSize: '0.875rem',
        }}>
          🚧 En développement — Phase suivante
        </div>
      </div>
    );
  };
}

function PageLoader() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
      <div style={{ width: '24px', height: '24px', border: '2px solid var(--border-color)', borderTopColor: 'var(--accent-blue)', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <PageLoader />;
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <ThemeProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route path="/" element={
          <PrivateRoute>
            <AppShell />
          </PrivateRoute>
        }>
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
          <Route path="webhooks" element={<WebhooksPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="plugins" element={<PluginsPage />} />
          <Route path="themes" element={<ThemesPage />} />
          <Route path="abm" element={
            <Suspense fallback={<PageLoader />}>
              <ABMPage />
            </Suspense>
          } />
          <Route path="crm-sync" element={
            <Suspense fallback={<PageLoader />}>
              <CRMSyncPage />
            </Suspense>
          } />
        </Route>

        {/* 404 */}
        <Route path="*" element={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg-primary)', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ fontSize: '4rem' }}>404</div>
            <p style={{ color: 'var(--text-muted)' }}>Page introuvable</p>
            <a href="/" style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}>← Retour au dashboard</a>
          </div>
        } />
      </Routes>
    </BrowserRouter>
    </ThemeProvider>
  );
}
