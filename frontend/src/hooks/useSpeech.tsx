import { createContext, useContext, useState, useRef, useCallback, type ReactNode } from 'react';

const CHUNK_SIZE = 150;

interface SpeechAPI {
  speakNow: (text: string) => void;
  pause: () => void;
  resume: () => void;
  fastForward: (on: boolean) => void;
  isPlaying: boolean;
  isPaused: boolean;
}

const SpeechCtx = createContext<SpeechAPI | null>(null);

export function SpeechProvider({ children }: { children: ReactNode }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const queueRef = useRef<string[]>([]);
  const idxRef = useRef(0);
  const rateRef = useRef(2.0);
  const cancelFlag = useRef(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const speakNext = useCallback(() => {
    if (idxRef.current >= queueRef.current.length) {
      setIsPlaying(false);
      setIsPaused(false);
      return;
    }
    const text = queueRef.current[idxRef.current];
    idxRef.current++;

    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'zh-CN';
    utter.rate = rateRef.current;
    utter.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const zhVoice = voices.find(v => v.lang.startsWith('zh-CN') || v.lang.startsWith('zh'));
    if (zhVoice) utter.voice = zhVoice;

    utter.onend = () => speakNext();
    utter.onerror = () => {
      if (cancelFlag.current) { cancelFlag.current = false; return; }
      queueRef.current = []; idxRef.current = 0;
      setIsPlaying(false); setIsPaused(false);
    };

    window.speechSynthesis.speak(utter);
  }, []);

  const splitChunks = useCallback((text: string): string[] => {
    const chunks: string[] = [];
    let remaining = text;
    while (remaining.length > 0) {
      if (remaining.length <= CHUNK_SIZE) { chunks.push(remaining); break; }
      let splitAt = CHUNK_SIZE;
      for (let i = CHUNK_SIZE - 1; i >= CHUNK_SIZE / 2; i--) {
        if (/[，。！？；：、\n]/.test(remaining[i])) { splitAt = i + 1; break; }
      }
      chunks.push(remaining.slice(0, splitAt));
      remaining = remaining.slice(splitAt);
    }
    return chunks;
  }, []);

  // Server TTS fallback for mobile browsers that don't support speechSynthesis
  const speakServer = useCallback(async (text: string) => {
    if (cancelFlag.current) return;
    try {
      const res = await fetch('/speak?text=' + encodeURIComponent(text));
      if (!res.ok) throw new Error('TTS failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.pause();
        URL.revokeObjectURL(audioRef.current.src);
      }
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(url);
        audioRef.current = null;
      };
      audio.onerror = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(url);
        audioRef.current = null;
      };
      await audio.play();
    } catch {
      setIsPlaying(false);
    }
  }, []);

  const speakNow = useCallback((text: string) => {
    if (!text) return;
    cancelFlag.current = true;
    window.speechSynthesis?.cancel();

    // Detect if browser TTS is available (desktop Chrome/Edge support it well)
    const hasVoices = window.speechSynthesis && window.speechSynthesis.getVoices().length > 0;

    if (hasVoices) {
      // Browser TTS
      queueRef.current = splitChunks(text);
      idxRef.current = 0;
      rateRef.current = 2.5;
      setIsPlaying(true);
      setIsPaused(false);
      setTimeout(() => speakNext(), 60);
    } else {
      // Server TTS fallback
      setIsPlaying(true);
      speakServer(text);
    }
  }, [speakNext, splitChunks, speakServer]);

  const pause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPaused(true);
    } else {
      window.speechSynthesis?.pause();
      setIsPaused(true);
    }
  }, []);

  const resume = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.play();
      setIsPaused(false);
    } else {
      window.speechSynthesis?.resume();
      setIsPaused(false);
    }
  }, []);

  const fastForward = useCallback((on: boolean) => {
    if (audioRef.current) {
      audioRef.current.playbackRate = on ? 2.0 : 1.0;
      return;
    }

    const startIdx = Math.max(0, idxRef.current - 1);
    const remaining = queueRef.current.slice(startIdx);
    if (remaining.length === 0) return;

    cancelFlag.current = true;
    window.speechSynthesis?.cancel();

    rateRef.current = on ? 3.0 : 2.5;
    queueRef.current = remaining;
    idxRef.current = 0;
    setIsPaused(false);

    setTimeout(() => speakNext(), 60);
  }, [speakNext]);

  return (
    <SpeechCtx.Provider value={{ speakNow, pause, resume, fastForward, isPlaying, isPaused }}>
      {children}
    </SpeechCtx.Provider>
  );
}

export function useSpeech(): SpeechAPI {
  const ctx = useContext(SpeechCtx);
  if (!ctx) throw new Error('useSpeech must be used within SpeechProvider');
  return ctx;
}
