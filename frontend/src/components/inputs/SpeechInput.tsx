import { useState, useEffect, useRef } from 'react';
import { useGame } from '../../context/GameContext';

export function SpeechInput() {
  const { state, sendAction } = useGame();
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const interrupt = state?.interrupt;
  const prevInterruptRef = useRef(interrupt);

  useEffect(() => {
    if (interrupt !== prevInterruptRef.current) {
      setSubmitting(false);
      prevInterruptRef.current = interrupt;
    }
  }, [interrupt]);

  if (!interrupt || interrupt.type !== 'speech') return null;

  const previous = interrupt.previous_speeches || '（第一位发言者）';
  const role = interrupt.human_role || '?';
  const elimInfo = interrupt.eliminated_info || '无';

  const handleSubmit = async () => {
    if (!text.trim() || submitting) return;
    setSubmitting(true);
    await sendAction(text.trim());
    setText('');
  };

  return (
    <div className="bg-gradient-to-r from-red-950/20 to-red-900/10 border-2 border-red-500/40 rounded-xl p-5 mb-4 animate-pulse-glow transition-all duration-300">
      <h3 className="text-red-300 font-bold mb-2">
        📰 轮到发言 (身份: {role})
      </h3>
      <details className="mb-3">
        <summary className="text-gray-400 text-xs cursor-pointer hover:text-gray-300 transition-colors">之前发言</summary>
        <pre className="text-gray-500 text-xs mt-2 bg-night/50 p-3 rounded-lg max-h-40 overflow-y-auto whitespace-pre-wrap">{previous}</pre>
      </details>
      <p className="text-gray-500 text-xs mb-2">已淘汰: {elimInfo}</p>
      <textarea
        className="w-full bg-night border border-night-border rounded-lg px-4 py-3 text-gray-200 text-sm focus:outline-none focus:border-red-500 resize-none transition-colors disabled:opacity-40"
        rows={3}
        placeholder="输入你的发言..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
        disabled={submitting}
      />
      {submitting && (
        <div className="flex items-center gap-2 text-red-300 text-sm mt-2 animate-pulse">
          <div className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
          发言已提交，等待中...
        </div>
      )}
      <button
        className="mt-2 w-full bg-red-600 hover:bg-red-500 text-white rounded-lg py-2.5 font-medium transition-all duration-200 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
        onClick={handleSubmit}
        disabled={!text.trim() || submitting}
      >
        提交发言
      </button>
    </div>
  );
}