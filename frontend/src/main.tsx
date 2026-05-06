import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import ErrorBoundary from './ErrorBoundary.tsx';
import './index.css';

// ----------------------------------------------------------------------------
// Capture des erreurs très précoces (avant le rendu React)
// Utile en prod pour distinguer "écran noir" = JS pas chargé vs JS crashé
// ----------------------------------------------------------------------------
window.addEventListener('error', (event) => {
  console.error('[window.error] Erreur globale capturée:', event.error || event.message);
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('[unhandledrejection] Promise rejetée non gérée:', event.reason);
});

// ----------------------------------------------------------------------------
// Bootstrap React
// ----------------------------------------------------------------------------
const rootElement = document.getElementById('root');
if (!rootElement) {
  // Si #root est absent, on affiche directement un message lisible
  document.body.innerHTML =
    '<div style="padding:2rem;font-family:sans-serif;color:#fff;background:#111;min-height:100vh">' +
    '<h1>Erreur critique</h1><p>L\'élément racine #root est absent du DOM. Vérifiez index.html.</p>' +
    '</div>';
  throw new Error('Root element #root not found');
}

try {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>,
  );
} catch (error) {
  console.error('[bootstrap] Erreur au démarrage de React:', error);
  rootElement.innerHTML =
    '<div style="padding:2rem;font-family:sans-serif;color:#fff;background:#111;min-height:100vh">' +
    '<h1>Erreur de démarrage</h1>' +
    '<p>Impossible de démarrer l\'application. Voir la console (F12) pour les détails.</p>' +
    '<pre style="background:#222;padding:1rem;overflow:auto;border-radius:4px">' +
    String(error) +
    '</pre></div>';
}
