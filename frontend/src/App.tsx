import { useEffect } from 'react';
import { SpeechProvider } from './hooks/useSpeech';
import { GameProvider, useGame } from './context/GameContext';
import { useSSE } from './hooks/useSSE';
import { Layout } from './components/Layout';

function GameSync() {
  const { state, updateState, reset } = useGame();
  // Only connect SSE if game is not finished
  const sseGameId = state?.game_id && state?.status !== 'finished' ? state.game_id : null;
  useSSE(sseGameId, updateState, reset);

  // Recover from URL on page refresh
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const gid = params.get('game');
    if (gid && !state?.game_id) {
      fetch('/game/' + gid + '/debug')
        .then(r => {
          if (!r.ok) {
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
            _dismissedGameOver: d.status === 'finished' ? true : false,
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
