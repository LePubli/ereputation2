import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { Toaster } from './components/ui/Toast';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Pipeline from './pages/Pipeline';
import Plugins from './pages/Plugins';
import Prospects from './pages/Prospects';
import Settings from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<Login />} />

            {/* Protégées */}
            <Route path="/" element={
              <ProtectedRoute>
                <AppShell>
                  <Dashboard />
                </AppShell>
              </ProtectedRoute>
            } />
            <Route path="/pipeline" element={
              <ProtectedRoute><AppShell><Pipeline /></AppShell></ProtectedRoute>
            } />
            <Route path="/prospects" element={
              <ProtectedRoute><AppShell><Prospects /></AppShell></ProtectedRoute>
            } />
            <Route path="/plugins" element={
              <ProtectedRoute><AppShell><Plugins /></AppShell></ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute><AppShell><Settings /></AppShell></ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </BrowserRouter>
      <Toaster />
    </QueryClientProvider>
  );
}
