import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { Toaster } from './components/ui/Toast';
import Dashboard from './pages/Dashboard';
import Pipeline from './pages/Pipeline';
import Plugins from './pages/Plugins';
import Prospects from './pages/Prospects';
import Settings from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <AppShell>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/pipeline" element={<Pipeline />} />
              <Route path="/prospects" element={<Prospects />} />
              <Route path="/plugins" element={<Plugins />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Dashboard />} />
            </Routes>
          </AppShell>
        </ErrorBoundary>
      </BrowserRouter>
      <Toaster />
    </QueryClientProvider>
  );
}
