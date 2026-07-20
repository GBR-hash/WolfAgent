import { useState, useEffect, useRef } from 'react';
import { useGame } from '../../context/GameContext';

export function VoteResultPanel() {
  const { state, sendAction } = useGame();
  const interrupt = state?.interrupt;
  const [submitting, setSubmitting] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const prevInterruptRef = useRef(interrupt);

  useEffect(() => {
    if (interrupt !== prevInterruptRef.current) {
      setSubmitting(false);
      setDismissed(false);  // re-show on new vote_result
      prevInterruptRef.current = interrupt;
    }
  }, [interrupt]);

  if (!interrupt || interrupt.type !== 'vote_result' || dismissed) return null;

  const voteLines = interrupt.vote_lines || '';
  const countLines = interrupt.count_lines || '';
  const eliminatedPlayer = interrupt.eliminated_player;
  const eliminatedInfo = interrupt.eliminated_info || '';
  const roundNum = interrupt.round_num || state?.game_round || 1;

  const handleContinue = async () => {
    if (submitting) return;
    setSubmitting(true);
    await sendAction('ok');
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-night-card border-2 border-amber-500/40 rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl animate-scale-in">
        <div className="text-center mb-4">
          <div className="text-4xl mb-2">🗳</div>
          <h2 className="text-2xl font-bold text-amber-300 mb-1">第{roundNum}轮 投票结果</h2>
        </div>

        {/* Vote lines */}
        <div className="bg-night/80 rounded-xl p-4 mb-4">
          <div className="flex flex-wrap gap-2 mb-3">
            {voteLines.split('\n').filter(Boolean).map((line, i) => {
              const isHuman = line.includes('玩家7');
              return (
                <span
                  key={i}
                  className={
                    'inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs ' +
                    (isHuman
                      ? 'bg-red-950/30 border border-red-500/50 text-red-300'
                      : 'bg-night-card border border-night-border text-gray-300')
                  }
                >
                  {line}
                </span>
              );
            })}
          </div>

          {/* Counts */}
          {countLines && (
            <div className="text-sm text-amber-400 font-medium mb-3">
              票数: {countLines}
            </div>
          )}

          {/* Eliminated */}
          {eliminatedPlayer ? (
            <div className="bg-red-950/30 border border-red-500/30 rounded-xl px-4 py-3 text-center">
              <p className="text-red-300 font-bold text-lg">⚰ {eliminatedInfo} 被投票淘汰</p>
            </div>
          ) : (
            <div className="bg-gray-700/20 border border-gray-500/30 rounded-xl px-4 py-3 text-center">
              <p className="text-gray-300 text-sm">平票，无人被淘汰</p>
            </div>
          )}
        </div>

        <button
          className="w-full bg-amber-600 hover:bg-amber-500 text-white rounded-xl py-3 text-base font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-amber-600/25 disabled:opacity-50"
          onClick={handleContinue}
          disabled={submitting}
        >
          {submitting ? '确认中请稍后' : '▶ 继续'}
        </button>
      </div>
    </div>
  );
}
