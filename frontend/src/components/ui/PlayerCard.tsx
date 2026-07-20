import type { PlayerData } from '../../types/game';
import { roleEmoji, roleName } from '../../utils/role';

interface PlayerCardProps {
  player: PlayerData;
  isHuman: boolean;
  showRole: boolean;
}

export function PlayerCard({ player, isHuman, showRole }: PlayerCardProps) {
  const alive = player.is_alive;
  return (
    <div className={
      'flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ' +
      (alive
        ? 'bg-night-card border border-night-border'
        : 'bg-night-card/40 border border-night-border/30 opacity-60')
    }>
      <span className="text-base">{alive ? '✅' : '💀'}</span>
      <span className={alive ? 'text-gray-200' : 'text-gray-500 line-through'}>
        玩家{player.player_id}
      </span>
      {showRole ? (
        <span className="text-sm">
          {roleEmoji(player.role)} {roleName(player.role)}
        </span>
      ) : (
        <span className="text-sm text-gray-600" title="淘汰后揭晓身份">💑</span>
      )}
      {isHuman && <span className="text-red-400 text-xs ml-auto">⭐真人</span>}
    </div>
  );
}
