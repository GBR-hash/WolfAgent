import { useState, useEffect, useRef } from 'react';
import { useGame } from '../../context/GameContext';

export function VoteInput() {
  const { state, sendAction } = useGame();
  const interrupt = state?.interrupt;
  const [submitting, setSubmitting] = useState(false);
  const prevInterruptRef = useRef(interrupt);

  useEffect(() => {
    if (interrupt !== prevInterruptRef.current) {
      setSubmitting(false);
      prevInterruptRef.current = interrupt;
    }
  }, [interrupt]);

  if (!interrupt || interrupt.type !== 'vote') return null;

  const targets = interrupt.valid_targets || [];
  const speechesSummary = interrupt.speeches_summary || '';
  const elimInfo = interrupt.eliminated_info || '无';

  const handleVote = async (action: string) => {
    if (submitting) return;
    setSubmitting(true);
    await sendAction(action);
  };

  return (
    <div className="bg-gradient-to-r from-amber-950/20 to-amber-900/10 border-2 border-amber-500/40 rounded-xl p-5 mb-4 animate-pulse-glow transition-all duration-300">
      <h3 className="text-amber-300 font-bold mb-2">🗳 请投票淘汰</h3>
      <details className="mb-3">
        <summary className="text-gray-400 text-xs cursor-pointer hover:text-gray-300 transition-colors">全部发言</summary>
        <pre className="text-gray-500 text-xs mt-2 bg-night/50 p-3 rounded-lg max-h-40 overflow-y-auto whitespace-pre-wrap">{speechesSummary}</pre>
      </details>
      <p className="text-gray-500 text-xs mb-3">已淘汰: {elimInfo}</p>

      {submitting && (
        <div className="flex items-center gap-2 text-amber-300 text-sm mb-3 animate-pulse">
          <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
          投票已提交，等待中...
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {targets.map((t: number) => (
          <button
            key={t}
            className="bg-amber-600/20 hover:bg-amber-600/40 border border-amber-500/30 text-amber-200 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-[1.05] active:scale-[0.95] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            onClick={() => handleVote(String(t))}
            disabled={submitting}
          >
            玩家{t}
          </button>
        ))}
        <button
          className="bg-gray-600/20 hover:bg-gray-600/40 border border-gray-500/30 text-gray-300 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-[1.05] active:scale-[0.95] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
          onClick={() => handleVote('弃权')}
          disabled={submitting}
        >
          弃权
        </button>
      </div>
    </div>
  );
}
