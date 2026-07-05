import { useState, useEffect, useRef } from 'react';
import { useGame } from '../../context/GameContext';
import type { SecretChatMsg } from '../../types/game';

export function WerewolfChat() {
  const { state, sendAction } = useGame();
  const interrupt = state?.interrupt;
  const [chatText, setChatText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const prevInterruptRef = useRef(interrupt);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const interruptChat: SecretChatMsg[] = interrupt?.secret_chat || [];
  const stateChat: SecretChatMsg[] = state?._werewolf_secret_chat || [];
  const secretChat: SecretChatMsg[] = interruptChat.length >= stateChat.length ? interruptChat : stateChat;
  const validTargets: number[] = interrupt?.valid_targets || [];
  const partner: number[] = interrupt?.partner || [];

  useEffect(() => {
    const el = chatContainerRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    if (isNearBottom) {
      el.scrollTop = el.scrollHeight;
    }
  }, [secretChat.length]);

  useEffect(() => {
    if (interrupt !== prevInterruptRef.current) {
      setSubmitting(false);
      prevInterruptRef.current = interrupt;
    }
  }, [interrupt]);

  if (!interrupt || interrupt.type !== 'werewolf_discuss') return null;

  const handleSendChat = async () => {
    if (!chatText.trim() || submitting) return;
    const msg = chatText.trim();
    const payload = /^\d+$/.test(msg) ? msg : 'chat: ' + msg;
    setSubmitting(true);
    await sendAction(payload);
    setChatText('');
  };

  const handleKill = async (target: number) => {
    if (submitting) return;
    setSubmitting(true);
    await sendAction(String(target));
  };

  return (
    <div className="bg-gradient-to-r from-red-950/20 to-red-900/10 border-2 border-red-500/40 rounded-xl p-5 mb-4 animate-pulse-glow transition-all duration-300">
      <h3 className="text-red-300 font-bold mb-2">
        🐺 秘密频道 · 与队友讨论
      </h3>
      <p className="text-gray-500 text-xs mb-3">
        队友: 玩家{partner.join(', ')}
      </p>

      <div ref={chatContainerRef} className="bg-night/80 rounded-lg p-3 mb-3 max-h-48 overflow-y-auto space-y-2">
        {secretChat.length === 0 && (
          <p className="text-gray-600 text-xs text-center">等待队友发言...</p>
        )}
        {secretChat.map((msg: SecretChatMsg, i: number) => {
          const isMe = msg.from === 7;
          if (typeof msg.from === 'string' && msg.from === 'system') {
            return <p key={i} className="text-yellow-400 text-xs text-center">{msg.content}</p>;
          }
          return (
            <div key={i} className={'flex ' + (isMe ? 'justify-end' : 'justify-start')}>
              <div className={
                'max-w-[85%] rounded-lg px-3 py-2 text-sm ' +
                (isMe ? 'bg-green-900/40 text-green-200' : 'bg-gray-700/40 text-gray-200')
              }>
                <span className="text-xs opacity-60">{isMe ? '你' : '队友' + msg.from + '号'}:</span>
                <p className="mt-0.5">{msg.content}</p>
              </div>
            </div>
          );
        })}
      </div>

      {submitting && (
        <div className="flex items-center gap-2 text-red-300 text-sm mb-3 animate-pulse">
          <div className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
          消息已发送，等待回复...
        </div>
      )}

      <div className="flex gap-2 mb-3">
        <input
          className="flex-1 bg-night border border-night-border rounded-lg px-3 py-2 text-gray-200 text-sm focus:outline-none focus:border-red-500 transition-colors disabled:opacity-40"
          placeholder="输入消息讨论，或直接输入数字杀人"
          value={chatText}
          onChange={(e) => setChatText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSendChat(); } }}
          disabled={submitting}
        />
        <button
          className="bg-red-600/30 hover:bg-red-600/50 border border-red-500/30 text-red-200 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-[1.05] active:scale-[0.95] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
          onClick={handleSendChat}
          disabled={!chatText.trim() || submitting}
        >
          发送
        </button>
      </div>

      <p className="text-gray-500 text-xs mb-2">选择击杀目标：</p>
      <div className="flex flex-wrap gap-2">
        {validTargets.map((t: number) => (
          <button
            key={t}
            className="bg-red-700/30 hover:bg-red-700/60 border border-red-600/40 text-red-200 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-[1.05] active:scale-[0.95] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            onClick={() => handleKill(t)}
            disabled={submitting}
          >
            杀玩家{t}
          </button>
        ))}
      </div>
    </div>
  );
}