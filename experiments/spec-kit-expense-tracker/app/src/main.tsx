import { createRoot } from 'react-dom/client';
import App from './App';
import { isDemoMode } from './demo/demoData';
import './styles.css';

createRoot(document.getElementById('root')!).render(
  <App demo={isDemoMode(window.location.search)} />,
);

window.addEventListener('pageshow', (event) => {
  if (event.persisted) {
    window.location.reload();
  }
});
