import { useState } from 'react';
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
import { winnerLabel, roleEmoji, roleName } from '../utils/role';
import type { PlayerData } from '../types/game';

function getPillDetail(state: any): string | null {
  const players = Object.values(state.players ?? {}) as PlayerData[];
  if (state.human_role === 'werewolf') {
    const partners = players.filter((p: PlayerData) => p.role === 'werewolf' && p.player_id !== 7);
    if (partners.length > 0) {
      return '队友: ' + partners.map((p: PlayerData) => (p.is_alive ? '✅' : '💀') + '玩家' + p.player_id).join(', ');
    }
  } else if (state.human_role === 'witch') {
    const h = state.witch_has_heal ? '✅' : '❌';
    const p = state.witch_has_poison ? '✅' : '❌';
    return '解药' + h + ' 毒药' + p;
  } else if (state.human_role === 'seer' && state.seer_check_target != null && state.seer_check_result) {
    return '查验玩家' + state.seer_check_target + '→' + state.seer_check_result;
  }
  return null;
}

export function Layout() {
  const { state } = useGame();
  const status = state?.status ?? 'idle';
  const phase = state?.phase ?? 'init';
  const dismissed = state?._dismissedGameOver ?? false;
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (status === 'idle') {
    return (
      <div className="h-screen bg-night text-gray-100">
        <HomePage />
      </div>
    );
  }

  const pillDetail = state ? getPillDetail(state) : null;
  const pillEmoji = state?.human_role ? roleEmoji(state.human_role) : '';
  const pillName = state?.human_role ? roleName(state.human_role) : '';
  const alive = state?.alive_players?.length ?? 0;
  const total = Object.keys(state?.players ?? {}).length;

  const statusBadge = status === 'running'
    ? <span className="text-blue-400 text-xs flex items-center gap-1"><span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />AI思考中</span>
    : status === 'waiting'
    ? <span className="text-amber-400 text-xs flex items-center gap-1"><span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-pulse" />等待操作</span>
    : status === 'finished'
    ? <span className="text-green-400 text-xs flex items-center gap-1"><span className="w-1.5 h-1.5 bg-green-400 rounded-full" />已结束</span>
    : null;

  return (
    <div className="flex h-screen bg-night text-gray-100">
      {/* Desktop sidebar */}
      <div className="hidden md:block flex-shrink-0">
        <Sidebar />
      </div>

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-30 bg-night-card/95 backdrop-blur-sm border-b border-night-border px-4 py-2.5 flex items-center justify-between">
        <h1 className="text-sm font-bold text-purple-300 flex items-center gap-1.5">
          🐺 WolfAgent
        </h1>
        {statusBadge}
      </div>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-4 md:p-6 pt-12 md:pt-0 pb-24 md:pb-0">
        {dismissed && state?.winner && (
          <div className="bg-gradient-to-r from-amber-900/30 via-amber-800/20 to-amber-900/30 border border-amber-600/40 rounded-xl px-4 py-3 md:px-6 md:py-4 mb-4 animate-slide-down flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div className="flex items-center gap-3">
              <span className="text-2xl md:text-3xl">🏆</span>
              <div>
                <div className="text-amber-300 font-bold text-base md:text-lg">{winnerLabel(state.winner)}</div>
                <div className="text-gray-400 text-xs md:text-sm">第{state.game_round}轮结束</div>
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

      {/* Mobile floating pill */}
      {status !== 'finished' && (
        <button
          className="md:hidden fixed bottom-4 left-1/2 -translate-x-1/2 z-30 bg-night-card/95 backdrop-blur-sm border border-night-border rounded-full px-4 py-2.5 shadow-lg shadow-black/30 flex items-center gap-2 text-xs active:scale-95 transition-transform"
          onClick={() => setSidebarOpen(true)}
        >
          <span>{pillEmoji}</span>
          <span className="text-gray-300 font-medium">{pillName}</span>
          {pillDetail && <span className="text-gray-500">| {pillDetail}</span>}
          <span className="text-gray-500">| 存活 {alive}/{total}</span>
        </button>
      )}
      {status === 'finished' && (
        <button
          className="md:hidden fixed bottom-4 left-1/2 -translate-x-1/2 z-30 bg-night-card/95 backdrop-blur-sm border border-amber-500/30 rounded-full px-4 py-2.5 shadow-lg shadow-black/30 flex items-center gap-2 text-xs active:scale-95 transition-transform"
          onClick={() => setSidebarOpen(true)}
        >
          <span>🏆</span>
          <span className="text-amber-300 font-medium">{state?.winner ? winnerLabel(state.winner) : ''}</span>
          <span className="text-gray-500">· 第{state?.game_round ?? 0}轮</span>
        </button>
      )}

      {/* Mobile bottom sheet overlay */}
      {sidebarOpen && (
        <>
          <div
            className="md:hidden fixed inset-0 z-50 bg-black/60 backdrop-blur-sm animate-fade-in"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="md:hidden fixed inset-x-0 bottom-0 z-50 animate-slide-up-bottom">
            <Sidebar variant="bottomsheet" onClose={() => setSidebarOpen(false)} />
          </div>
        </>
      )}
    </div>
  );
}
