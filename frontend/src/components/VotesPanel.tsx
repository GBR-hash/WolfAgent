import { useGame } from '../context/GameContext';
import { voteLabel } from '../utils/format';

export function VotesPanel() {
  const { state } = useGame();
  const votes = state?.votes ?? {};
  const entries = Object.entries(votes);
  if (!state || entries.length === 0) return null;

  const tally: Record<number, number> = {};
  entries.forEach(([, target]) => {
    const t = Number(target);
    if (t > 0) tally[t] = (tally[t] || 0) + 1;
  });

  return (
    <div className="mb-4 animate-fade-in">
      <h3 className="text-gray-400 text-xs uppercase tracking-wide mb-1">
        本轮投票 ({entries.length}票)
      </h3>
      {state.vote_order && state.vote_order.length > 0 && state.phase === 'day_vote' && (
        <div className="flex items-center gap-1 mb-2 flex-wrap">
          <span className="text-gray-600 text-xs">投票顺序:</span>
          {state.vote_order.map((pid: number, idx: number) => {
            const cursor = state.vote_cursor ?? 0;
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
      <div className="flex flex-wrap gap-2">
        {entries.map(([voter, target]) => {
          const v = Number(voter);
          const t = Number(target);
          const lbl = voteLabel(t);
          const isHuman = v === 7;
          return (
            <span
              key={voter}
              className={
                'inline-flex items-center gap-1 px-2 py-1 md:px-3 md:py-1.5 rounded-lg text-xs ' +
                (isHuman
                  ? 'bg-red-950/30 border border-red-500/50 text-red-300'
                  : 'bg-night-card border border-night-border text-gray-300')
              }
            >
              玩家{v} {lbl}
            </span>
          );
        })}
      </div>
      {Object.keys(tally).length > 0 && (
        <div className="mt-2 text-sm text-amber-300">
          票数: {Object.entries(tally)
            .sort((a, b) => b[1] - a[1])
            .map(([k, c]) => `玩家${k}:${c}票`)
            .join(' | ')}
        </div>
      )}
    </div>
  );
}
