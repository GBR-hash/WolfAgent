export type Role = 'werewolf' | 'witch' | 'seer' | 'villager';
export type Status = 'idle' | 'created' | 'running' | 'waiting' | 'finished' | 'error';

export interface PlayerData {
  player_id: number;
  role: Role;
  is_human: boolean;
  is_alive: boolean;
}

export interface SpeechEntry {
  player_id: number;
  content: string;
}

export interface LogEntry {
  type: string;
  message: string;
  round: number;
  player_id?: number;
  target?: number;
}

export interface SecretChatMsg {
  from: number;
  content: string;
}

export interface VoteTally {
  votes: Record<string, number>;
  counts: Record<number, number>;
  eliminated: number | null;
}

export interface InterruptData {
  type: 'speech' | 'vote' | 'witch_decision' | 'seer_check' | 'seer_result' | 'werewolf_discuss' | 'vote_result' | 'error';
  human_role?: string;
  player_id?: number;
  previous_speeches?: string;
  speeches_summary?: string;
  god_announcement?: string;
  valid_targets?: number[];
  valid_poison_targets?: number[];
  killed_target?: number;
  has_heal?: boolean;
  has_poison?: boolean;
  prompt?: string;
  game_round?: number;
  round_num?: number;
  partner?: number[];
  secret_chat?: SecretChatMsg[];
  alive_players?: number[];
  eliminated_players?: number[];
  eliminated_info?: string;
  message?: string;
  // vote_result fields
  vote_lines?: string;
  count_lines?: string;
  eliminated_player?: number | null;
  // seer_result fields
  checked_player?: number;
  check_result?: string;
}

export interface UserInfo {
  user_id: number;
  username: string;
  token: string;
}

export interface GameState {
  game_id: string;
  status: Status;
  phase: string;
  game_round: number;
  players: Record<string, PlayerData>;
  alive_players: number[];
  eliminated_players: number[];
  eliminated_roles: Record<string, string>;
  _night_killed_ids: number[];
  god_announcement: string;
  speeches: SpeechEntry[];
  votes: Record<string, number>;
  human_role: Role | null;
  human_alive: boolean;
  is_waiting: boolean;
  interrupt: InterruptData | null;
  winner: string | null;
  game_log: LogEntry[];
  speech_cursor: number;
  vote_cursor: number;
  speech_order: number[];
  vote_order: number[];
  werewolf_kill_target: number | null;
  witch_heal_target: number | null;
  witch_poison_target: number | null;
  seer_check_target: number | null;
  seer_check_result: string | null;
  witch_has_heal: boolean | null;
  witch_has_poison: boolean | null;
  _dismissedGameOver?: boolean;
  user?: UserInfo | null;
  speeches_history?: Record<number, SpeechEntry[]>;
  votes_history?: Record<number, Record<string, number>>;
  _werewolf_secret_chat?: SecretChatMsg[];
  night_step?: number;
}
