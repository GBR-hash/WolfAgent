import { useRef, useEffect } from 'react';
import { useSpeech } from '../hooks/useSpeech';
import { useGame } from '../context/GameContext';
import type { SpeechEntry } from '../types/game';

export function SpeechesPanel() {
  const { state } = useGame();
  if (!state) return null;
  const speeches = state?.speeches ?? [];
  const bottomRef = useRef<HTMLDivElement>(null);

  const { speakNow } = useSpeech();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [speeches.length]);

  if (speeches.length === 0) return null;

  return (
    <div className="mb-4 animate-fade-in">
      <h3 className="text-gray-400 text-xs uppercase tracking-wide mb-1">
        本轮发言 ({speeches.length}条)
      </h3>
      {state.speech_order && state.speech_order.length > 0 && state.phase === 'day_speeches' && (
        <div className="flex items-center gap-1 mb-2 flex-wrap">
          <span className="text-gray-600 text-xs">发言顺序:</span>
          {state.speech_order.map((pid: number, idx: number) => {
            const cursor = state.speech_cursor ?? 0;
            const isCurrent = idx === cursor;
            const isPast = idx < cursor;
            return (
              <span key={pid} className="flex items-center gap-0.5">
                {idx > 0 && <span className="text-gray-700 text-xs">→</span>}
                <span className={
                  'text-xs px-1.5 py-0.5 rounded transition-all ' +
                  (isCurrent ? 'bg-amber-500/20 text-amber-300 font-bold' :
                   isPast ? 'text-gray-500' : 'text-gray-600')
                }>
                  玩家{pid}
                </span>
              </span>
            );
          })}
        </div>
      )}
      <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
        {speeches.map((sp: SpeechEntry, i: number) => {
          const isHuman = sp.player_id === 7;
          return (
            <div
              key={i}
              className={
                'rounded-lg px-4 py-3 text-sm border-l-[3px] ' +
                (isHuman
                  ? 'bg-red-950/20 border-red-500'
                  : 'bg-night-card border-blue-500/50')
              }
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className={isHuman ? 'text-red-400' : 'text-blue-300'}>
                    玩家{sp.player_id}发言：
                  </span>
                  <span className="text-gray-300 ml-1">{sp.content}</span>
                </div>
                {!isHuman && (
                  <button
                    onClick={() => speakNow(sp.content)}
                    className="text-gray-500 hover:text-amber-400 text-xs flex-shrink-0 mt-0.5 transition-colors"
                    title="播报此条发言 (2x)"
                  >
                    🔊
                  </button>
                )}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
