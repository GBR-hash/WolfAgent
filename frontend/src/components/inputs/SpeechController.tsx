import { useSpeech } from '../../hooks/useSpeech';

export function SpeechController() {
  const { isPlaying, isPaused, pause, resume, fastForward } = useSpeech();

  if (!isPlaying) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-night-card border border-amber-500/30 rounded-2xl px-5 py-3 shadow-2xl shadow-amber-500/10 flex items-center gap-4 animate-slide-up">
      <span className="text-gray-400 text-xs">语音播报</span>

      <button
        onClick={isPaused ? resume : pause}
        className="text-amber-400 hover:text-amber-300 text-lg transition-colors w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5"
        title={isPaused ? '继续' : '暂停'}
      >
        {isPaused ? '▶' : '⏸'}
      </button>

      <button
        onMouseDown={() => fastForward(true)}
        onMouseUp={() => fastForward(false)}
        onMouseLeave={() => fastForward(false)}
        onTouchStart={() => fastForward(true)}
        onTouchEnd={() => fastForward(false)}
        className="text-gray-400 hover:text-amber-400 text-lg transition-colors w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 select-none"
        title="长按以3倍速快进"
      >
        ⏩
      </button>
    </div>
  );
}
