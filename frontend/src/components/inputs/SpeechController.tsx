import { useSpeech } from '../../hooks/useSpeech';

function SoundBars() {
  return (
    <span className="flex items-end gap-[2px] h-4">
      <span className="inline-block w-[3px] bg-amber-400 rounded-sm animate-sound-bar" style={{ animationDelay: '0s', height: '60%' }} />
      <span className="inline-block w-[3px] bg-amber-400 rounded-sm animate-sound-bar" style={{ animationDelay: '0.15s', height: '100%' }} />
      <span className="inline-block w-[3px] bg-amber-400 rounded-sm animate-sound-bar" style={{ animationDelay: '0.3s', height: '40%' }} />
      <span className="inline-block w-[3px] bg-amber-400 rounded-sm animate-sound-bar" style={{ animationDelay: '0.45s', height: '80%' }} />
    </span>
  );
}

export function SpeechController() {
  const { isPlaying, isPaused, isLoading, pause, resume } = useSpeech();

  if (!isPlaying) return null;

  return (
    <>
      <style>{`
        @keyframes sound-bar {
          0%, 100% { transform: scaleY(0.4); }
          50% { transform: scaleY(1); }
        }
        .animate-sound-bar {
          animation: sound-bar 0.6s ease-in-out infinite;
          transform-origin: bottom;
        }
      `}</style>
      <div className="fixed bottom-20 md:bottom-6 left-1/2 -translate-x-1/2 z-50 bg-night-card border border-amber-500/30 rounded-2xl px-5 py-3 shadow-2xl shadow-amber-500/10 flex items-center gap-3 animate-slide-up">
        {isLoading ? (
          <>
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-1.5 h-1.5 bg-amber-400 rounded-full animate-pulse" />
              <span className="inline-block w-1.5 h-1.5 bg-amber-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
              <span className="inline-block w-1.5 h-1.5 bg-amber-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
            </span>
            <span className="text-amber-300/80 text-xs">生成语音中...</span>
          </>
        ) : isPaused ? (
          <>
            <span className="text-gray-400 text-xs">已暂停</span>
            <button
              onClick={resume}
              className="text-amber-400 hover:text-amber-300 text-lg transition-colors w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5"
              title="继续播放"
            >
              ▶
            </button>
          </>
        ) : (
          <>
            <SoundBars />
            <span className="text-amber-300/80 text-xs">播放中</span>
            <button
              onClick={pause}
              className="text-amber-400 hover:text-amber-300 text-lg transition-colors w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5"
              title="暂停"
            >
              ⏸
            </button>
          </>
        )}
      </div>
    </>
  );
}
