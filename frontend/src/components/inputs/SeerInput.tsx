import { useState, useEffect, useRef } from 'react';
import { useGame } from '../../context/GameContext';

export function SeerInput() {
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

  // ---- seer_result: show check result ----
  if (interrupt && interrupt.type === 'seer_result') {
    const checkedPlayer = interrupt.checked_player;
    const checkResult = interrupt.check_result || '?';
    const isWolf = checkResult === '狼人';

    const handleContinue = async () => {
      if (submitting) return;
      setSubmitting(true);
      await sendAction('ok');
    };

    return (
      <div className="bg-gradient-to-r from-blue-950/20 to-blue-900/10 border-2 border-blue-500/40 rounded-xl p-5 mb-4 animate-scale-in transition-all duration-300">
        <h3 className="text-blue-300 font-bold mb-3">🔮 查验结果</h3>
        <div className="bg-night/80 rounded-xl p-4 mb-4 text-center">
          <p className="text-gray-300 text-lg mb-2">
            玩家 <strong className="text-blue-300">{checkedPlayer}</strong> 的身份是：
          </p>
          <p className={'text-3xl font-bold ' + (isWolf ? 'text-red-400' : 'text-green-400')}>
            {isWolf ? '🐺 狼人' : '💑 好人'}
          </p>
        </div>
        {submitting && (
          <div className="flex items-center gap-2 text-blue-300 text-sm mb-3 animate-pulse justify-center">
            <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
            确认中...
          </div>
        )}
        <button
          className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded-xl py-3 text-base font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-blue-600/25 disabled:opacity-50"
          onClick={handleContinue}
          disabled={submitting}
        >
          ▶ 确认
        </button>
      </div>
    );
  }

  // ---- seer_check: choose a player ----
  if (!interrupt || interrupt.type !== 'seer_check') return null;

  const targets: number[] = interrupt.valid_targets || [];

  const handleCheck = async (target: number) => {
    if (submitting) return;
    setSubmitting(true);
    await sendAction(String(target));
  };

  return (
    <div className="bg-gradient-to-r from-blue-950/20 to-blue-900/10 border-2 border-blue-500/40 rounded-xl p-5 mb-4 animate-pulse-glow transition-all duration-300">
      <h3 className="text-blue-300 font-bold mb-2">🔮 预言家查验</h3>
      <p className="text-gray-400 text-sm mb-3">选择要查验的玩家：</p>

      {submitting && (
        <div className="flex items-center gap-2 text-blue-300 text-sm mb-3 animate-pulse">
          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          查验已提交，等待中...
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {targets.map((t: number) => (
          <button
            key={t}
            className="bg-blue-600/20 hover:bg-blue-600/40 border border-blue-500/30 text-blue-200 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-[1.05] active:scale-[0.95] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            onClick={() => handleCheck(t)}
            disabled={submitting}
          >
            查验玩家{t}
          </button>
        ))}
      </div>
    </div>
  );
}
