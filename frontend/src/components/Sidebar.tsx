import React, { useEffect, useState } from 'react';
import { useGame } from '../context/GameContext';
import { PlayerCard } from './ui/PlayerCard';
import { roleEmoji, roleName } from '../utils/role';
import { fetchRecords } from '../api/client';

interface RecordItem {
  id: number;
  game_id: string;
  human_role: string;
  winner: string | null;
  total_rounds: number;
  is_alive: boolean;
  created_at: string;
}

export function Sidebar() {
  const { state, startGame, reset, loginAction, logoutAction } = useGame();
  const [loading, setLoading] = React.useState(false);
  const [recordsOpen, setRecordsOpen] = useState(false);
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [recordsLoading, setRecordsLoading] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const user = state?.user;
  const players = state?.players ?? {};
  const humanRole = state?.human_role;
  const isFinished = state?.status === 'finished';
  const sorted = Object.values(players).sort((a, b) => a.player_id - b.player_id);

  const wolfPartners = humanRole === 'werewolf'
    ? sorted.filter(p => p.role === 'werewolf' && p.player_id !== 7)
    : [];

  const shouldShowRole = (p: typeof sorted[0]) => {
    if (isFinished) return true;
    if (!p.is_alive) return true;
    return false;
  };

  useEffect(() => {
    if (recordsOpen && user && records.length === 0) {
      setRecordsLoading(true);
      fetchRecords()
        .then(d => setRecords(d.records || []))
        .catch(() => {})
        .finally(() => setRecordsLoading(false));
    }
  }, [recordsOpen, user]);

  const handleStart = async () => {
    setLoading(true);
    try {
      const result = await startGame('random');
      window.history.replaceState(null, '', '?game=' + result.game_id);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <>
    <aside className="w-72 bg-night-card border-r border-night-border flex flex-col h-screen">
      <div className="p-4 border-b border-night-border">
        <h1 className="text-xl font-bold text-purple-300 flex items-center gap-2">
          🐺 WolfAgent
        </h1>
        <p className="text-gray-500 text-xs mt-1">AI 狼人杀 · LangGraph</p>
      </div>

      {user && (
        <div className="px-4 py-2 border-b border-night-border bg-green-500/5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-green-300">
              💑 欢迎, {user.username}
            </p>
            <button
              className="text-gray-500 hover:text-red-400 text-xs transition-colors"
              onClick={() => setShowLogoutConfirm(true)}
            >
              退出
            </button>
          </div>
        </div>
      )}

      {state?.game_id && (
        <div className="p-3 border-b border-night-border">
          <button
            className="w-full bg-purple-600 hover:bg-purple-500 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
            onClick={() => { reset(); window.history.replaceState(null, '', '/'); }}
            disabled={loading}
          >
            🔧 新游戏
          </button>
        </div>
      )}

      {humanRole && (
        <div className="px-4 py-3 border-b border-night-border bg-purple-500/10">
          <p className="text-sm text-purple-300">
            {roleEmoji(humanRole)} 你是 <strong>{roleName(humanRole)}</strong> (玩家7)
            {wolfPartners.length > 0 && (
              <span className="text-purple-400/80">
                {' | 队友 '}
                {wolfPartners.map((p, i) => (
                  <span key={p.player_id}>
                    {i > 0 && ', '}
                    <span className={p.is_alive ? '' : 'line-through opacity-60'}>
                      玩家{p.player_id}
                    </span>
                  </span>
                ))}
              </span>
            )}
          </p>
        </div>
      )}

      {sorted.length > 0 && (
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <p className="text-gray-400 text-xs uppercase tracking-wide mb-2">玩家状态</p>
          {sorted.map((p) => (
            <PlayerCard
              key={p.player_id}
              player={p}
              isHuman={p.is_human}
              showRole={shouldShowRole(p)}
            />
          ))}
          {!isFinished && sorted.filter(p => p.is_alive).length > 1 && (
            <p className="text-gray-600 text-xs text-center mt-2">淘汰后才显示身份</p>
          )}
        </div>
      )}

      {user && (
        <div className="border-t border-night-border">
          <button
            className="w-full px-4 py-2.5 text-left text-gray-400 hover:text-gray-200 text-sm font-medium transition-colors flex items-center justify-between"
            onClick={() => setRecordsOpen(!recordsOpen)}
          >
            📋 我的战绩
            <span className="text-xs">{recordsOpen ? '▲' : '▼'}</span>
          </button>
          {recordsOpen && (
            <div className="max-h-64 overflow-y-auto px-3 pb-3 space-y-1">
              {recordsLoading && <p className="text-gray-500 text-xs text-center py-2">加载中...</p>}
              {!recordsLoading && records.length === 0 && <p className="text-gray-600 text-xs text-center py-2">暂无记录</p>}
              {records.map(r => (
                <div key={r.id}>
                  <div
                    className="w-full text-left px-2 py-1.5 rounded text-xs"
                  >
                    <span className="text-gray-300">{roleEmoji(r.human_role)} {roleName(r.human_role)}</span>
                    <span className={'ml-2 ' + (r.winner === 'werewolf' ? 'text-red-400' : r.winner === 'villager' ? 'text-green-400' : 'text-gray-500')}>
                      {r.winner === (r.human_role === 'werewolf' ? 'werewolf' : 'villager') ? '✅' : '❌'}
                    </span>
                    <span className="text-gray-500 ml-2">{r.total_rounds}轮</span>
                    <span className="text-gray-600 ml-2 text-[10px]">{r.created_at?.slice(0, 10)}</span>
                  </div>

                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="p-3 border-t border-night-border text-center">
        <p className="text-gray-600 text-xs">WolfAgent · DeepSeek</p>
      </div>
    </aside>
      {showLogoutConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowLogoutConfirm(false)}>
          <div className="bg-night-card border border-night-border rounded-xl p-6 shadow-2xl max-w-sm w-full mx-4" onClick={e => e.stopPropagation()}>
            <p className="text-gray-200 text-lg font-medium mb-2">确定退出吗？</p>
            <p className="text-gray-500 text-sm mb-5">退出后将返回首页，当前游戏进度不会保存。</p>
            <div className="flex gap-3 justify-end">
              <button
                className="px-4 py-2 rounded-lg text-sm text-gray-300 hover:bg-night/50 transition-colors"
                onClick={() => setShowLogoutConfirm(false)}
              >
                取消
              </button>
              <button
                className="px-4 py-2 rounded-lg text-sm bg-red-600 hover:bg-red-500 text-white transition-colors"
                onClick={() => { logoutAction(); window.location.href = '/'; }}
              >
                确定退出
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
