import type { Role } from '../types/game';

export const ROLE_EMOJI: Record<string, string> = {
  werewolf: '🐺',
  witch: '🧪',
  seer: '🔮',
  villager: '💑',
};

export const ROLE_NAME: Record<string, string> = {
  werewolf: '狼人',
  witch: '女巫',
  seer: '预言家',
  villager: '村民',
};

export function roleEmoji(role: string): string {
  return ROLE_EMOJI[role] || '?';
}

export function roleName(role: string): string {
  return ROLE_NAME[role] || role;
}

export function winnerLabel(winner: string | null): string {
  if (winner === 'werewolf') return '🐺 狼人阵营';
  if (winner === 'villager') return '💑 好人阵营';
  return winner || '?';
}
