import { createContext, useContext, useState, useRef, useCallback, useEffect, type ReactNode } from 'react';

interface SpeechAPI {
  speakNow: (text: string) => void;
  pause: () => void;
  resume: () => void;
  isPlaying: boolean;
  isPaused: boolean;
  isLoading: boolean;
}

const SpeechCtx = createContext<SpeechAPI | null>(null);

let _unlocked = false;

function unlockAudio() {
  if (_unlocked) return;
  try {
    const AudioCtx = (window as any).AudioContext || (window as any).webkitAudioContext;
    if (AudioCtx) {
      const ctx = new AudioCtx();
      const buf = ctx.createBuffer(1, 1, 22050);
      const src = ctx.createBufferSource();
      src.buffer = buf;
      src.connect(ctx.destination);
      src.start(0);
      if (ctx.state === 'suspended') ctx.resume();
    }
    _unlocked = true;
  } catch {}
}

export function SpeechProvider({ children }: { children: ReactNode }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const handler = () => unlockAudio();
    const events = ['touchstart', 'touchend', 'click'];
    events.forEach(e => document.addEventListener(e, handler, { once: true }));
    return () => events.forEach(e => document.removeEventListener(e, handler));
  }, []);

  const speakNow = useCallback((text: string) => {
    if (!text) return;

    unlockAudio();

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.removeAttribute('src');
      audioRef.current.load();
      if (audioRef.current.parentNode) {
        audioRef.current.parentNode.removeChild(audioRef.current);
      }
      audioRef.current = null;
    }

    const audio = document.createElement('audio');
    audio.setAttribute('playsinline', '');
    audio.setAttribute('webkit-playsinline', '');
    audio.preload = 'auto';
    audio.src = '/speak?text=' + encodeURIComponent(text);
    audio.style.display = 'none';
    document.body.appendChild(audio);
    audioRef.current = audio;

    setIsPlaying(true);
    setIsPaused(false);
    setIsLoading(true);

    audio.load();

    let played = false;
    const tryPlay = () => {
      if (played) return;
      played = true;
      setIsLoading(false);
      audio.play().catch((e: any) => {
        console.warn('play rejected:', e && e.name);
        setIsPlaying(false);
      });
    };

    audio.oncanplay = tryPlay;
    audio.oncanplaythrough = tryPlay;
    audio.onended = () => setIsPlaying(false);
    audio.onerror = () => { setIsPlaying(false); setIsLoading(false); };

    setTimeout(() => { if (!played) tryPlay(); }, 5000);
  }, []);

  const pause = useCallback(() => {
    const a = audioRef.current;
    if (a && !a.paused) {
      a.pause();
      setIsPaused(true);
    }
  }, []);

  const resume = useCallback(() => {
    const a = audioRef.current;
    if (a && a.paused && a.src && a.src !== window.location.href) {
      a.play().catch(() => {});
      setIsPaused(false);
    }
  }, []);

  return (
    <SpeechCtx.Provider value={{ speakNow, pause, resume, isPlaying, isPaused, isLoading }}>
      {children}
    </SpeechCtx.Provider>
  );
}

export function useSpeech(): SpeechAPI {
  const ctx = useContext(SpeechCtx);
  if (!ctx) throw new Error('useSpeech must be used within SpeechProvider');
  return ctx;
}
