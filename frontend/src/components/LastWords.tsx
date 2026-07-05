import { useGame } from '../context/GameContext';
import type { LogEntry } from '../types/game';

export function LastWords() {
  const { state } = useGame();
  const logs: LogEntry[] = state?.game_log ?? [];
  const lastWordsLog = logs.find(l => l.type === 'last_words');

  if (!lastWordsLog) return null;

  return (
    <div className="mb-4 animate-fade-in">
      <div className="bg-gradient-to-r from-purple-950/40 via-fuchsia-900/30 to-purple-950/40 border-2 border-purple-500/50 rounded-xl p-5 shadow-lg shadow-purple-500/10">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-2xl">💀</span>
          <h3 className="text-purple-300 font-bold text-base">
            玩家{lastWordsLog.player_id} 的遗言
          </h3>
        </div>
        <div className="bg-black/30 border border-purple-500/20 rounded-lg px-4 py-3">
          <p className="text-purple-100 text-sm leading-relaxed italic">
            {(lastWordsLog.message || '').replace(/^第1晚遗言\(玩家\d+\):\s*/, '') || lastWordsLog.message}
          </p>
        </div>
        <p className="text-purple-600 text-xs mt-2">
          第1晚被狼人杀害，这是最后的遗言
        </p>
      </div>
    </div>
  );
}