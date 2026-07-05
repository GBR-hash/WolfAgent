import { useState, useEffect, useRef } from 'react';
import { useGame } from '../../context/GameContext';

export function LastWordsInput() {
  const { state, sendAction } = useGame();
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const interrupt = state?.interrupt;
  const prevInterruptRef = useRef(interrupt);

  useEffect(() => {
    if (interrupt !== prevInterruptRef.current) {
      setSubmitting(false);
      setText('');
      prevInterruptRef.current = interrupt;
    }
  }, [interrupt]);

  if (!interrupt || interrupt.type !== 'last_words') return null;

  const handleSubmit = async () => {
    const msg = text.trim() || '我没什么要说的。';
    if (submitting) return;
    setSubmitting(true);
    await sendAction(msg);
    setText('');
  };

  return (
    <div className="bg-gradient-to-r from-purple-950/40 via-fuchsia-900/30 to-purple-950/40 border-2 border-purple-500/50 rounded-xl p-5 mb-4 animate-pulse-glow shadow-lg shadow-purple-500/10">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">💀</span>
        <h3 className="text-purple-300 font-bold text-lg">
          你在第1晚被狼人杀害了
        </h3>
      </div>
      <p className="text-gray-400 text-sm mb-3">
        这是你的遗言机会，50字以内。你可以选择暴露或隐瞒自己的真实身份。
      </p>
      <textarea
        className="w-full bg-black/30 border border-purple-500/30 rounded-lg px-4 py-3 text-purple-100 text-sm focus:outline-none focus:border-purple-400 resize-none transition-colors disabled:opacity-40 placeholder-gray-600"
        rows={3}
        maxLength={50}
        placeholder="输入你的遗言（50字以内）..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
        disabled={submitting}
      />
      <div className="flex items-center justify-between mt-2">
        <span className="text-gray-500 text-xs">{text.length}/50</span>
        {submitting && (
          <div className="flex items-center gap-2 text-purple-300 text-sm animate-pulse">
            <div className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
            遗言已提交，等待中...
          </div>
        )}
      </div>
      <button
        className="mt-2 w-full bg-purple-700 hover:bg-purple-600 text-white rounded-lg py-2.5 font-medium transition-all duration-200 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
        onClick={handleSubmit}
        disabled={submitting}
      >
        提交遗言{!text.trim() ? '（默认：我没什么要说的）' : ''}
      </button>
    </div>
  );
}