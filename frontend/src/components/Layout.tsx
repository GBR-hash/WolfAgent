import { Sidebar } from './Sidebar';
import { PhaseBanner } from './PhaseBanner';
import { GodAnnouncement } from './GodAnnouncement';
import { SpeechesPanel } from './SpeechesPanel';
import { VotesPanel } from './VotesPanel';
import { NightLog } from './NightLog';
import { Timeline } from './Timeline';
import { GameOverModal } from './GameOverModal';
import { LoadingSpinner } from './ui/LoadingSpinner';
import { SpeechInput } from './inputs/SpeechInput';
import { VoteInput } from './inputs/VoteInput';
import { WitchInput } from './inputs/WitchInput';
import { SeerInput } from './inputs/SeerInput';
import { WerewolfChat } from './inputs/WerewolfChat';
import { LastWords } from './LastWords';
import { LastWordsInput } from './inputs/LastWordsInput';
import { VoteResultPanel } from './inputs/VoteResultPanel';
import { SpeechController } from './inputs/SpeechController';
import { HomePage } from './HomePage';
import { useGame } from '../context/GameContext';
import { winnerLabel } from '../utils/role';

export function Layout() {
  const { state } = useGame();
  const status = state?.status ?? 'idle';
  const phase = state?.phase ?? 'init';
  const dismissed = state?._dismissedGameOver ?? false;

  // Homepage: full-screen, no sidebar
  if (status === 'idle') {
    return (
      <div className="h-screen bg-night text-gray-100">
        <HomePage />
      </div>
    );
  }

  // In-game: sidebar + main area
  return (
    <div className="flex h-screen bg-night text-gray-100">
      <Sidebar />

      <main className="flex-1 overflow-y-auto p-6">
        {dismissed && state?.winner && (
          <div className="bg-gradient-to-r from-amber-900/30 via-amber-800/20 to-amber-900/30 border border-amber-600/40 rounded-xl px-6 py-4 mb-4 animate-slide-down flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🏆</span>
              <div>
                <div className="text-amber-300 font-bold text-lg">{winnerLabel(state.winner)}</div>
                <div className="text-gray-400 text-sm">第{state.game_round}轮结束</div>
              </div>
            </div>
            <div className="flex gap-2">
              {state.human_alive && (
                <span className="text-green-400 text-xs bg-green-950/40 px-2 py-1 rounded-full">你存活到最后</span>
              )}
              {!state.human_alive && (
                <span className="text-red-400 text-xs bg-red-950/40 px-2 py-1 rounded-full">你已被淘汰</span>
              )}
            </div>
          </div>
        )}

        <PhaseBanner />
        <GodAnnouncement />
        <LastWords />

        {/* Vote result overlay - shown between day_vote and night */}
        <VoteResultPanel />
        <SpeechController />

        <SpeechInput />
        <VoteInput />
        <WitchInput />
        <SeerInput />
        <WerewolfChat />
        <LastWordsInput />

        {status === 'running' && phase === 'night' && (
          <LoadingSpinner text="AI 思考中（狼人讨论/女巫/预言家）..." />
        )}
        {status === 'running' && phase.startsWith('day') && !state?.is_waiting && (
          <LoadingSpinner text="AI 计算中..." />
        )}

        <NightLog />
        <SpeechesPanel />
        <VotesPanel />
        <Timeline />

        <GameOverModal />
      </main>
    </div>
  );
}
