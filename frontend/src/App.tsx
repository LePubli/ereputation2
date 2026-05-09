import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { Toaster } from './components/ui/Toast';

const Dashboard      = lazy(() => import('./pages/Dashboard'));
const Login          = lazy(() => import('./pages/Login'));
const TableView      = lazy(() => import('./pages/TableView'));
const Pipeline       = lazy(() => import('./pages/Pipeline'));
const Prospects      = lazy(() => import('./pages/Prospects'));
const Plugins        = lazy(() => import('./pages/Plugins'));
const Settings       = lazy(() => import('./pages/Settings'));
const WebhooksPage   = lazy(() => import('./pages/WebhooksPage'));
const SequencerPage  = lazy(() => import('./pages/SequencerPage'));
const SignalsPage     = lazy(() => import('./pages/SignalsPage'));
const InboundPage    = lazy(() => import('./pages/InboundPage'));
const ABMPage        = () => <ComingSoon name="ABM & TAM" />;
const ContactIntelPage = lazy(() => import('./pages/ContactIntelPage'));
const AIAgentPage    = lazy(() => import('./pages/AIAgentPage'));
const CRMPage        = () => <ComingSoon name="CRM Sync" />;
const AnalyticsPage  = lazy(() => import('./pages/Analytics').catch(() => ({ default: () => <ComingSoon name="Analytics" /> })));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 } },
});

function Loading() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 12 }}>
      <div style={{ width: 20, height: 20, border: '2px solid var(--brand-200)', borderTopColor: 'var(--brand)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      <span style={{ color: 'var(--tx-muted)', fontSize: 14 }}>Chargement…</span>
    </div>
  );
}

function ComingSoon({ name }: { name: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 12 }}>
      <div style={{ fontSize: 48 }}>🚧</div>
      <h2 style={{ fontWeight: 600, color: 'var(--tx-primary)' }}>{name}</h2>
      <p style={{ color: 'var(--tx-muted)', fontSize: 14 }}>Module en cours de déploiement</p>
    </div>
  );
}

function Protected({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AppShell>
        <Suspense fallback={<Loading />}>{children}</Suspense>
      </AppShell>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <Routes>
            <Route path="/login"      element={<Suspense fallback={<Loading />}><Login /></Suspense>} />
            <Route path="/"           element={<Protected><Dashboard /></Protected>} />
            <Route path="/table"      element={<Protected><TableView /></Protected>} />
            <Route path="/pipeline"   element={<Protected><Pipeline /></Protected>} />
            <Route path="/prospects"  element={<Protected><Prospects /></Protected>} />
            <Route path="/plugins"    element={<Protected><Plugins /></Protected>} />
            <Route path="/settings"   element={<Protected><Settings /></Protected>} />
            <Route path="/webhooks"   element={<Protected><WebhooksPage /></Protected>} />
            <Route path="/sequences"  element={<Protected><SequencerPage /></Protected>} />
            <Route path="/signals"    element={<Protected><SignalsPage /></Protected>} />
            <Route path="/inbound"    element={<Protected><InboundPage /></Protected>} />
            <Route path="/abm"        element={<Protected><ABMPage /></Protected>} />
            <Route path="/contacts"   element={<Protected><ContactIntelPage /></Protected>} />
            <Route path="/agent"      element={<Protected><AIAgentPage /></Protected>} />
            <Route path="/crm"        element={<Protected><CRMPage /></Protected>} />
            <Route path="/analytics"  element={<Protected><AnalyticsPage /></Protected>} />
            <Route path="*"           element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </BrowserRouter>
      <Toaster />
    </QueryClientProvider>
  );
}
