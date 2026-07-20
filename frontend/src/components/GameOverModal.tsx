import { useGame } from '../context/GameContext';
import { roleEmoji, roleName, winnerLabel } from '../utils/role';
import type { PlayerData } from '../types/game';

export function GameOverModal() {
  const { state, reset, dismissGameOver } = useGame();
  if (!state || state.status !== 'finished') return null;
  if (state._dismissedGameOver) return null;

  const players = Object.values(state.players ?? {}).sort(
    (a: PlayerData, b: PlayerData) => a.player_id - b.player_id
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="bg-night-card border border-night-border rounded-2xl p-8 max-w-lg w-full mx-4 shadow-2xl animate-scale-in">
        <div className="text-center mb-4">
          <div className="text-5xl mb-3">🏆</div>
          <h2 className="text-3xl font-bold text-gold mb-2">
            {winnerLabel(state.winner)}
          </h2>
          <p className="text-gray-400">游戏结束 · 第{state.game_round}轮</p>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-6">
          {players.map((p: PlayerData) => (
            <div
              key={p.player_id}
              className={
                'rounded-xl px-4 py-3 border text-center transition-all duration-300 ' +
                (p.is_alive
                  ? 'bg-green-950/20 border-green-700/30'
                  : 'bg-red-950/20 border-red-700/30')
              }
            >
              <div className="text-lg">{roleEmoji(p.role)}</div>
              <div className="text-sm font-medium text-gray-200">
                玩家{p.player_id}
              </div>
              <div className="text-xs text-gray-400">{roleName(p.role)}</div>
              {p.is_human && <div className="text-xs text-red-400 mt-1">⭐真人</div>}
              <div className={'text-xs mt-1 ' + (p.is_alive ? 'text-green-400' : 'text-red-400')}>
                {p.is_alive ? '存活' : '淘汰'}
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            className="flex-1 bg-gray-700/50 hover:bg-gray-700/80 border border-gray-600/30 text-gray-300 rounded-xl px-4 py-3 font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
            onClick={dismissGameOver}
          >
            稍后再看
          </button>
          <button
            className="flex-[2] bg-purple-600 hover:bg-purple-500 text-white rounded-xl px-4 py-3 font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-purple-600/25"
            onClick={reset}
          >
            🔧 再来一局
          </button>
        </div>
      </div>
    </div>
  );
}
