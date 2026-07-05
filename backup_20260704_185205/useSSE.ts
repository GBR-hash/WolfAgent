import { useEffect, useRef } from 'react';
import { createSSEConnection } from '../api/client';
import type { GameState } from '../types/game';

export function useSSE(
  gameId: string | null,
  onState: (state: GameState) => void,
  onReset?: () => void,
) {
  const esRef = useRef<EventSource | null>(null);
  const errorCountRef = useRef(0);
  const finishedRef = useRef(false);

  useEffect(() => {
    if (!gameId) return;

    errorCountRef.current = 0;
    finishedRef.current = false;

    const es = createSSEConnection(
      gameId,
      (state) => {
        errorCountRef.current = 0;
        const gs = state as GameState;
        onState(gs);
        // Game finished - close SSE connection cleanly to prevent reconnect loop
        if (gs.status === 'finished' && esRef.current) {
          finishedRef.current = true;
          console.log('Game finished, closing SSE connection');
          esRef.current.close();
        }
      },
      (_err: Event) => {
        // Ignore errors after game finished (normal connection close)
        if (finishedRef.current) return;
        errorCountRef.current++;
        console.error('SSE error (#' + errorCountRef.current + '):', _err);
        // Only reset after 6 consecutive errors with exponential backoff
        if (errorCountRef.current >= 6 && onReset) {
          console.warn('SSE persistent failure, resetting...');
          es.close();
          window.history.replaceState({}, '', window.location.pathname);
          onReset();
        }
      },
    );
    esRef.current = es;

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [gameId]);

  return esRef;
}
