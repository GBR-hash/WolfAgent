import { useEffect } from 'react';
import { SpeechProvider } from './hooks/useSpeech';
import { GameProvider, useGame } from './context/GameContext';
import { useSSE } from './hooks/useSSE';
import { Layout } from './components/Layout';

function GameSync() {
  const { state, updateState, reset } = useGame();
  useSSE(state?.game_id || null, updateState, reset);

  // Recover from URL on page refresh
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const gid = params.get('game');
    if (gid && !state?.game_id) {
      fetch('/game/' + gid + '/debug')
        .then(r => {
          if (!r.ok) {
            // Game no longer exists (server restarted) - clear URL and reset
            console.warn('Game ' + gid + ' not found, resetting...');
            window.history.replaceState({}, '', '/');
            reset();
            return null;
          }
          return r.json();
        })
        .then(d => {
          if (!d) return;
          updateState({
            ...d.state,
            game_id: gid,
            status: d.status,
            is_waiting: d.is_waiting,
            interrupt: d.interrupt,
            human_role: d.state?.players?.['7']?.role || null,
          });
        })
        .catch(err => {
          console.error('Recovery failed:', err);
          window.history.replaceState({}, '', '/');
          reset();
        });
    }
  }, []);

  return null;
}

function App() {
  return (
    <GameProvider>
      <SpeechProvider>
        <GameSync />
        <Layout />
      </SpeechProvider>
    </GameProvider>
  );
}

export default App;
