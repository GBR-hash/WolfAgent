import { useGame } from '../context/GameContext';
import type { LogEntry } from '../types/game';

const SHOW_TYPES = new Set([
  'round_start',
  'death_night',
  'peace_night',
  'elimination',
  'tie',
  'game_over',
  'eliminate_done',
  'last_words',
]);

export function NightLog() {
  const { state } = useGame();
  const logs: LogEntry[] = (state?.game_log ?? []).filter(l => SHOW_TYPES.has(l.type));
  if (logs.length === 0) return null;

  return (
    <div className="mb-4 animate-fade-in">
      <h3 className="text-gray-400 text-xs uppercase tracking-wide mb-2">
        游戏日志
      </h3>
      <div className="space-y-1 max-h-40 overflow-y-auto">
        {logs.map((l: LogEntry, i: number) => {
          const isElim = l.type === 'death_night' || l.type === 'elimination';
          const isLastWords = l.type === 'last_words';
          const isGameOver = l.type === 'game_over';
          return (
            <div
              key={i}
              className={'text-xs flex gap-2 rounded-lg px-2 py-1 ' +
                (isGameOver ? 'text-amber-300 font-medium' : isLastWords ? 'text-purple-300 bg-purple-950/30 border border-purple-500/30' : isElim ? 'text-red-300' : 'text-gray-500')}
            >
              <span className="text-gray-600 shrink-0">[第{l.round}轮]</span>
              <span>{l.message}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
