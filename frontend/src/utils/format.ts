export function truncate(text: string, maxLen: number = 80): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen) + '...';
}

export function phaseLabel(phase: string): string {
  const map: Record<string, string> = {
    init: '初始化',
    night: '夜晚阶段',
    day_announcement: '白天·公告',
    day_speeches: '白天·发言',
    day_vote: '白天·投票',
    game_over: '游戏结束',
  };
  return map[phase] || phase;
}

export function phaseClass(phase: string): string {
  if (phase.startsWith('night')) return 'text-blue-300';
  if (phase.startsWith('day')) return 'text-amber-300';
  if (phase === 'game_over') return 'text-green-300';
  return 'text-gray-300';
}

export function voteLabel(v: number): string {
  if (v === -1 || v === null || v === undefined) return '弃权';
  return '→ 玩家' + v;
}
