import { useState, useEffect, useRef } from 'react';
import { useGame } from '../../context/GameContext';

export function WitchInput() {
  const { state, sendAction } = useGame();
  const interrupt = state?.interrupt;
  const [submitting, setSubmitting] = useState(false);
  const prevInterruptRef = useRef(interrupt);
  const [poisonTarget, setPoisonTarget] = useState(0);

  useEffect(() => {
    if (interrupt !== prevInterruptRef.current) {
      setSubmitting(false);
      prevInterruptRef.current = interrupt;
    }
  }, [interrupt]);

  if (!interrupt || interrupt.type !== 'witch_decision') return null;

  const killed = interrupt.killed_target;
  const hasHeal = interrupt.has_heal ?? false;
  const hasPoison = interrupt.has_poison ?? false;
  const poisonTargets: number[] = interrupt.valid_poison_targets || [];

  if (poisonTarget === 0 && poisonTargets.length > 0) {
    setPoisonTarget(poisonTargets[0]);
  }

  const handleAction = async (action: string) => {
    if (submitting) return;
    setSubmitting(true);
    await sendAction(action);
  };

  return (
    <div className="bg-gradient-to-r from-purple-950/20 to-purple-900/10 border-2 border-purple-500/40 rounded-xl p-5 mb-4 animate-pulse-glow transition-all duration-300">
      <h3 className="text-purple-300 font-bold mb-2">🧪 女巫决策</h3>
      <p className="text-gray-300 text-sm mb-4">
        🐺 狼人今晚击杀了 <strong className="text-red-400">玩家{killed}</strong>
      </p>
      <p className="text-gray-500 text-xs mb-4">
        解药: {hasHeal ? '✅ 可用' : '❌ 已用'} | 毒药: {hasPoison ? '✅ 可用' : '❌ 已用'}
      </p>

      {submitting && (
        <div className="flex items-center gap-2 text-purple-300 text-sm mb-3 animate-pulse">
          <div className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
          操作已发送，等待中...
        </div>
      )}

      <div className="grid grid-cols-3 gap-3">
        {hasHeal ? (
          <button
            className="bg-green-600/20 hover:bg-green-600/40 border border-green-500/30 text-green-200 rounded-lg py-3 text-sm font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            onClick={() => handleAction('save')}
            disabled={submitting}
          >
            💉 救活玩家{killed}
          </button>
        ) : (
          <button className="bg-gray-700/20 border border-gray-600/20 text-gray-500 rounded-lg py-3 text-sm" disabled>
            💉 解药已用
          </button>
        )}
        {hasPoison && poisonTargets.length > 0 ? (
          <div className="flex flex-col gap-2">
            <select
              className="bg-night border border-night-border rounded-lg px-2 py-2 text-gray-200 text-xs disabled:opacity-40"
              value={poisonTarget}
              onChange={(e) => setPoisonTarget(Number(e.target.value))}
              disabled={submitting}
            >
              {poisonTargets.map((t: number) => (
                <option key={t} value={t}>玩家{t}</option>
              ))}
            </select>
            <button
              className="bg-red-600/20 hover:bg-red-600/40 border border-red-500/30 text-red-200 rounded-lg py-2 text-sm font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
              onClick={() => handleAction('poison ' + poisonTarget)}
              disabled={submitting}
            >
              ☠️ 毒杀
            </button>
          </div>
        ) : (
          <button className="bg-gray-700/20 border border-gray-600/20 text-gray-500 rounded-lg py-3 text-sm" disabled>
            ☠️ {hasPoison ? '无可毒目标' : '毒药已用'}
          </button>
        )}
        <button
          className="bg-gray-600/20 hover:bg-gray-600/40 border border-gray-500/30 text-gray-300 rounded-lg py-3 text-sm font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
          onClick={() => handleAction('skip')}
          disabled={submitting}
        >
          ⏭️ 跳过
        </button>
      </div>
    </div>
  );
}
