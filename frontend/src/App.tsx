import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { Spinner } from './components/ui/Spinner';
import { Toaster } from './components/ui/Toast';

const Dashboard    = lazy(() => import('./pages/Dashboard'));
const Login        = lazy(() => import('./pages/Login'));
const TableView    = lazy(() => import('./pages/TableView'));
const Pipeline     = lazy(() => import('./pages/Pipeline'));
const Prospects    = lazy(() => import('./pages/Prospects'));
const Plugins      = lazy(() => import('./pages/Plugins'));
const Settings     = lazy(() => import('./pages/Settings'));
const WebhooksPage = lazy(() => import('./pages/WebhooksPage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 },
  },
});

const Loading = () => (
  <div className="flex items-center justify-center h-full min-h-64">
    <Spinner label="Chargement…" />
  </div>
);

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
            <Route path="/login" element={<Suspense fallback={<Loading />}><Login /></Suspense>} />
            <Route path="/"           element={<Protected><Dashboard /></Protected>} />
            <Route path="/table"      element={<Protected><TableView /></Protected>} />
            <Route path="/pipeline"   element={<Protected><Pipeline /></Protected>} />
            <Route path="/prospects"  element={<Protected><Prospects /></Protected>} />
            <Route path="/plugins"    element={<Protected><Plugins /></Protected>} />
            <Route path="/settings"   element={<Protected><Settings /></Protected>} />
            <Route path="/webhooks"   element={<Protected><WebhooksPage /></Protected>} />
            <Route path="*"           element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </BrowserRouter>
      <Toaster />
    </QueryClientProvider>
  );
}
