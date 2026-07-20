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

  const speakNow = useCallback((text: string) => {
    if (!text || !window.speechSynthesis) return;
    cancelFlag.current = true;
    window.speechSynthesis.cancel();
    queueRef.current = splitChunks(text);
    idxRef.current = 0;
    rateRef.current = 2.0;
    setIsPlaying(true);
    setIsPaused(false);
    setTimeout(() => speakNext(), 60);
  }, [speakNext, splitChunks]);

  const pause = useCallback(() => {
    window.speechSynthesis.pause();
    setIsPaused(true);
  }, []);

  const resume = useCallback(() => {
    window.speechSynthesis.resume();
    setIsPaused(false);
  }, []);

  const fastForward = useCallback((on: boolean) => {
    const remaining = queueRef.current.slice(idxRef.current);
    if (remaining.length === 0) return;

    cancelFlag.current = true;
    window.speechSynthesis.cancel();

    rateRef.current = on ? 3.0 : 2.0;
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
