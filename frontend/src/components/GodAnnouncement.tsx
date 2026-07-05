import { useGame } from '../context/GameContext';

export function GodAnnouncement() {
  const { state } = useGame();
  const ann = state?.god_announcement;
  if (!ann) return null;

  return (
    <div className="bg-gradient-to-r from-amber-900/20 to-yellow-900/10 border border-amber-700/30 rounded-xl px-5 py-3 mb-4 animate-fade-in">
      <p className="text-amber-200 text-sm font-medium">
        📙 {ann}
      </p>
    </div>
  );
}
