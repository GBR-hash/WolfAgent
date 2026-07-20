import { useState } from 'react';
import { useSpeech } from '../hooks/useSpeech';
import { useGame } from '../context/GameContext';
import { roleEmoji, roleName } from '../utils/role';
import type { SpeechEntry } from '../types/game';

export function Timeline() {
  const { state } = useGame();
  if (!state || state.status !== 'finished') return null;

  const speechesHistory: Record<number, SpeechEntry[]> = state.speeches_history || {};
  const votesHistory: Record<number, Record<string, number>> = state.votes_history || {};
  const eliminatedRoles: Record<string, string> = state.eliminated_roles || {};
  const rounds = Object.keys(speechesHistory).map(Number).sort((a, b) => a - b);

  // Default: expand last round
  const { speakNow } = useSpeech();

  const [expandedRounds, setExpandedRounds] = useState<Set<number>>(() => {
    const s = new Set<number>();
    if (rounds.length > 0) s.add(rounds[rounds.length - 1]);
    return s;
  });

  const toggleRound = (r: number) => {
    setExpandedRounds(prev => {
      const next = new Set(prev);
      if (next.has(r)) next.delete(r);
      else next.add(r);
      return next;
    });
  };

  if (rounds.length === 0) {
    return (
      <div className="mb-4">
        <h3 className="text-gray-400 text-xs uppercase tracking-wide mb-2">游戏全程回顾</h3>
        <p className="text-gray-600 text-sm">暂无记录</p>
      </div>
    );
  }

  return (
    <div className="mb-4 animate-fade-in">
      <h3 className="text-gray-400 text-xs uppercase tracking-wide mb-2">
        游戏全程回顾 ({rounds.length}轮)
      </h3>
      <div className="space-y-3">
        {rounds.map(round => {
          const sps = speechesHistory[round] || [];
          const votes = votesHistory[round] || {};
          const isExpanded = expandedRounds.has(round);

          // Count votes
          const tally: Record<number, number> = {};
          Object.values(votes).forEach((target: number) => {
            if (target > 0) tally[target] = (tally[target] || 0) + 1;
          });

          // Find who was eliminated this round
          let eliminatedPid: number | null = null;
          let maxVotes = 0;
          Object.entries(tally).forEach(([pid, count]) => {
            if (count > maxVotes) {
              maxVotes = count;
              eliminatedPid = Number(pid);
            } else if (count === maxVotes) {
              eliminatedPid = null; // tie
            }
          });

          return (
            <div key={round} className="bg-night-card border border-night-border rounded-xl overflow-hidden">
              <button
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors text-left"
                onClick={() => toggleRound(round)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-amber-300 text-sm font-bold">第{round}轮</span>
                  <span className="text-gray-500 text-xs">
                    {sps.length}条发言 / {Object.keys(votes).length}票
                  </span>
                  {eliminatedPid && (
                    <span className="text-red-400 text-xs">
                      ⚰ 玩家{eliminatedPid}被淘汰
                    </span>
                  )}
                </div>
                <span className="text-gray-500 text-sm">{isExpanded ? '▲' : '▼'}</span>
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 space-y-3 border-t border-night-border/50 pt-3 animate-fade-in">
                  {/* Speeches */}
                  {sps.length > 0 && (
                    <div>
                      <h4 className="text-gray-400 text-xs font-medium mb-2">📰 发言 ({sps.length}条)</h4>
                      <div className="space-y-2">
                        {sps.map((sp: SpeechEntry, i: number) => {
                          const isHuman = sp.player_id === 7;
                          return (
                            <div
                              key={i}
                              className={
                                'rounded-lg px-3 py-2 text-xs border-l-[3px] ' +
                                (isHuman
                                  ? 'bg-red-950/20 border-red-500'
                                  : 'bg-night/50 border-blue-500/50')
                              }
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <span className={isHuman ? 'text-red-400' : 'text-blue-300'}>
                                    玩家{sp.player_id}：
                                  </span>
                                  <span className="text-gray-300">{sp.content}</span>
                                </div>
                                {!isHuman && (
                                  <button
                                    onClick={(e) => { e.stopPropagation(); speakNow(sp.content); }}
                                    className="text-gray-500 hover:text-amber-400 text-xs flex-shrink-0 transition-colors"
                                    title="播报此条发言 (2x)"
                                  >
                                    🔊
                                  </button>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Votes */}
                  {Object.keys(votes).length > 0 && (
                    <div>
                      <h4 className="text-gray-400 text-xs font-medium mb-2">🗳 投票</h4>
                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {Object.entries(votes).map(([voter, target]) => {
                          const v = Number(voter);
                          const t = Number(target);
                          const isHuman = v === 7;
                          return (
                            <span
                              key={voter}
                              className={
                                'inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs ' +
                                (isHuman
                                  ? 'bg-red-950/30 border border-red-500/50 text-red-300'
                                  : 'bg-night/50 border border-night-border text-gray-300')
                              }
                            >
                              玩家{v} {t > 0 ? '→ 玩家' + t : '→ 弃权'}
                            </span>
                          );
                        })}
                      </div>
                      {Object.keys(tally).length > 0 && (
                        <div className="text-xs text-amber-400">
                          票数: {Object.entries(tally)
                            .sort((a, b) => b[1] - a[1])
                            .map(([k, c]) => `玩家${k}:${c}票`)
                            .join(' | ')}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Elimination */}
                  {eliminatedPid && (
                    <div className="bg-red-950/20 border border-red-500/20 rounded-lg px-3 py-2">
                      <span className="text-red-300 text-xs">
                        ⚰ 淘汰: {roleEmoji(eliminatedRoles[String(eliminatedPid)] || '?')} 玩家{eliminatedPid} ({roleName(eliminatedRoles[String(eliminatedPid)] || '?')})
                      </span>
                    </div>
                  )}
                  {!eliminatedPid && Object.keys(votes).length > 0 && (
                    <div className="bg-gray-700/20 border border-gray-500/20 rounded-lg px-3 py-2">
                      <span className="text-gray-400 text-xs">平票，无人淘汰</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* All eliminated players summary */}
      {Object.keys(eliminatedRoles).length > 0 && (
        <div className="mt-4 bg-night-card border border-night-border rounded-xl p-4">
          <h4 className="text-gray-400 text-xs font-medium mb-2">淘汰名单</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(eliminatedRoles).map(([pid, role]) => (
              <span key={pid} className="text-xs bg-night/50 border border-night-border rounded-lg px-2.5 py-1 text-gray-300">
                {roleEmoji(role)} 玩家{pid} ({roleName(role)})
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
