import { useGame } from '../context/GameContext';
import { phaseLabel, phaseClass } from '../utils/format';

type StepKey = 'night' | 'announce' | 'speech' | 'vote';

type NightStepKey = 'werewolf_kill' | 'witch_act' | 'seer_check';

const NIGHT_STEPS: { key: NightStepKey; label: string; icon: string }[] = [
  { key: 'werewolf_kill', label: '狼人行动', icon: '🐺' },
  { key: 'witch_act', label: '女巫决策', icon: '🧪' },
  { key: 'seer_check', label: '预言家查验', icon: '🔮' },
];

function getCurrentNightStep(interruptType: string | undefined, nightStep: number | undefined): NightStepKey | null {
  // Priority 1: interrupt type (precise, during human interaction)
  if (interruptType === 'werewolf_discuss') return 'werewolf_kill';
  if (interruptType === 'witch_decision') return 'witch_act';
  if (interruptType === 'seer_check') return 'seer_check';
  // Priority 2: night_step from backend (during non-interactive AI processing)
  if (nightStep === 0) return 'werewolf_kill';
  if (nightStep === 1) return 'witch_act';
  if (nightStep === 2) return 'seer_check';
  return null;
}

const STEPS: { key: StepKey; label: string; icon: string }[] = [
  { key: 'night', label: '夜晚', icon: '🌙' },
  { key: 'announce', label: '公告', icon: '📙' },
  { key: 'speech', label: '发言', icon: '📰' },
  { key: 'vote', label: '投票', icon: '🗳' },
];

function getCurrentStep(phase: string): StepKey | null {
  if (phase.startsWith('night')) return 'night';
  if (phase === 'day_announcement') return 'announce';
  if (phase === 'day_speeches') return 'speech';
  if (phase === 'day_vote') return 'vote';
  return null;
}

export function PhaseBanner() {
  const { state } = useGame();
  if (!state) return null;

  const phase = state.phase;
  const round = state.game_round;
  const label = phaseLabel(phase);
  const cls = phaseClass(phase);
  const currentStep = getCurrentStep(phase);
  const isGameOver = phase === 'game_over';

  const bgClass = phase.startsWith('night')
    ? 'bg-gradient-to-r from-[#0f0f2e] to-[#1a1030] border-blue-900/40'
    : phase.startsWith('day')
    ? 'bg-gradient-to-r from-[#1a120b] to-[#1f1508] border-amber-900/40'
    : phase === 'game_over'
    ? 'bg-gradient-to-r from-[#0f1a0f] to-[#102010] border-green-900/40'
    : 'bg-night-card border-night-border';

  return (
    <div className={bgClass + ' border rounded-xl px-6 py-4 mb-4 transition-all duration-500 animate-fade-in'}>
      <div className="flex items-center gap-3 mb-3">
        <span className={'text-xl md:text-2xl font-bold transition-colors duration-500 ' + cls}>{label}</span>
        {round > 0 && (
          <span className="text-gray-400 text-sm bg-night-card/50 px-3 py-1 rounded-full transition-all duration-300">
            第{round}轮
          </span>
        )}
        {state.status === 'running' && (
          <span className="ml-auto flex items-center gap-1.5 text-blue-400 text-sm">
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
            AI 思考中...
          </span>
        )}
        {state.status === 'waiting' && (
          <span className="ml-auto flex items-center gap-1.5 text-amber-400 text-sm animate-pulse">
            <span className="w-2 h-2 bg-amber-400 rounded-full" />
            等待你的操作
          </span>
        )}
        {state.status === 'finished' && (
          <span className="ml-auto flex items-center gap-1.5 text-green-400 text-sm">
            <span className="w-2 h-2 bg-green-400 rounded-full" />
            游戏结束
          </span>
        )}
      </div>

      {!isGameOver && phase !== 'init' && phase.startsWith('night') && (
        <div className="flex items-center gap-1">
          {NIGHT_STEPS.map((step, idx) => {
            const nightCurrent = getCurrentNightStep(state.interrupt?.type, state.night_step);
            const nightStepIdx = NIGHT_STEPS.findIndex(s => s.key === nightCurrent);
            const isCurrent = step.key === nightCurrent;
            const isPast = nightStepIdx > idx;
            const isRunning = state.status === 'running' && !nightCurrent;
            return (
              <div key={step.key} className="flex items-center gap-1 flex-1">
                {idx > 0 && (
                  <div className={'flex-1 h-0.5 rounded-full transition-all duration-500 ' +
                    (isPast || isCurrent ? 'bg-blue-500/60' : 'bg-gray-700/40')} />
                )}
                <div className={'flex items-center gap-1.5 px-2 py-1 rounded-lg transition-all duration-500 ' +
                  (isCurrent || isRunning
                    ? 'bg-blue-500/10 border border-blue-500/30 scale-110'
                    : isPast
                    ? 'bg-blue-500/5 border border-blue-500/10'
                    : 'bg-transparent border border-transparent')}>
                  <span className={'text-sm transition-all duration-500 ' +
                    (isCurrent || isRunning ? 'opacity-100' : isPast ? 'opacity-60' : 'opacity-30')}>
                    {step.icon}
                  </span>
                  <span className={'text-xs font-medium transition-all duration-300 ' +
                    (isCurrent ? 'text-blue-300' : isRunning ? 'text-blue-300 animate-pulse' : isPast ? 'text-blue-400/60' : 'text-gray-600')}>
                    {step.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!isGameOver && phase !== 'init' && !phase.startsWith('night') && currentStep && (
        <div className="flex items-center gap-1">
          {STEPS.map((step, idx) => {
            const isCurrent = step.key === currentStep;
            const isPast = STEPS.findIndex(s => s.key === currentStep) > idx;
            return (
              <div key={step.key} className="flex items-center gap-1 flex-1">
                {idx > 0 && (
                  <div className={'flex-1 h-0.5 rounded-full transition-all duration-500 ' +
                    (isPast || isCurrent ? 'bg-amber-500/60' : 'bg-gray-700/40')} />
                )}
                <div className={'flex items-center gap-1.5 px-2 py-1 rounded-lg transition-all duration-500 ' +
                  (isCurrent
                    ? 'bg-amber-500/10 border border-amber-500/30 scale-110'
                    : isPast
                    ? 'bg-amber-500/5 border border-amber-500/10'
                    : 'bg-transparent border border-transparent')}>
                  <span className={'text-sm transition-all duration-500 ' +
                    (isCurrent ? 'opacity-100' : isPast ? 'opacity-60' : 'opacity-30')}>
                    {step.icon}
                  </span>
                  <span className={'text-xs font-medium transition-all duration-300 ' +
                    (isCurrent ? 'text-amber-300' : isPast ? 'text-amber-400/60' : 'text-gray-600')}>
                    {step.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
