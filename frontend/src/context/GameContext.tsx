import React, { createContext, useContext, useReducer, useCallback, type ReactNode } from 'react';
import type { GameState, Role } from '../types/game';
import { newGame, submitAction } from '../api/client';

interface UserInfo {
  user_id: number;
  username: string;
  token: string;
}

interface ContextValue {
  state: GameState | null;
  startGame: (role: string, playStyle?: string) => Promise<{ game_id: string; human_role: string; message: string }>;
  sendAction: (action: string) => Promise<void>;
  updateState: (s: GameState) => void;
  reset: () => void;
  dismissGameOver: () => void;
  loginAction: (userId: number, username: string, token: string) => void;
  logoutAction: () => void;
}

const GameContext = createContext<ContextValue | null>(null);

const INITIAL: GameState = {
  game_id: '',
  status: 'idle',
  phase: 'init',
  game_round: 0,
  players: {},
  alive_players: [],
  eliminated_players: [],
  eliminated_roles: {},
  _night_killed_ids: [],
  god_announcement: '',
  speeches: [],
  votes: {},
  human_role: null,
  human_alive: true,
  is_waiting: false,
  interrupt: null,
  winner: null,
  game_log: [],
  speech_cursor: 0,
  vote_cursor: 0,
  speech_order: [],
  vote_order: [],
  werewolf_kill_target: null,
  witch_heal_target: null,
  witch_poison_target: null,
  seer_check_target: null,
  seer_check_result: null,
  witch_has_heal: null,
  witch_has_poison: null,
  _dismissedGameOver: false,
  user: null,
};

type Action =
  | { type: 'SET_STATE'; payload: Partial<GameState> }
  | { type: 'RESET' }
  | { type: 'DISMISS_GAME_OVER' }
  | { type: 'LOGIN'; payload: UserInfo }
  | { type: 'LOGOUT' };

function reducer(_state: GameState, action: Action): GameState {
  switch (action.type) {
    case 'SET_STATE':
      return { ..._state, ...action.payload };
    case 'RESET':
      return { ...INITIAL, user: _state.user };
    case 'DISMISS_GAME_OVER':
      return { ..._state, _dismissedGameOver: true };
    case 'LOGIN':
      localStorage.setItem('wolf_token', action.payload.token);
      return { ..._state, user: action.payload };
    case 'LOGOUT':
      localStorage.removeItem('wolf_token');
      return { ..._state, user: null };
    default:
      return _state;
  }
}

export function GameProvider({ children }: { children: ReactNode }) {
  // Try restore user from localStorage
  const savedToken = typeof window !== 'undefined' ? localStorage.getItem('wolf_token') : null;
  const initUser = savedToken ? (() => {
    try {
      const payload = JSON.parse(atob(savedToken.split('.')[1]));
      return { user_id: payload.user_id, username: payload.username, token: savedToken } as UserInfo;
    } catch { return null; }
  })() : null;

  const init = { ...INITIAL, user: initUser };
  const [state, dispatch] = useReducer(reducer, init);

  const updateState = useCallback((s: GameState) => {
    dispatch({ type: 'SET_STATE', payload: s });
  }, []);

  const startGame = useCallback(async (role: string, playStyle: string = 'balanced') => {
    dispatch({ type: 'RESET' });
    const result = await newGame(role, playStyle);
    // Persist game ID in URL so refresh restores the session
    window.history.replaceState({}, '', '/wolf/?game=' + result.game_id);
    dispatch({
      type: 'SET_STATE',
      payload: {
        ...INITIAL,
        game_id: result.game_id,
        human_role: result.human_role as Role,
        status: 'running' as const,
        user: state?.user || null,
      },
    });
    return result;
  }, [state?.user]);

  const sendAction = useCallback(async (action: string) => {
    if (!state || !state.game_id) return;
    await submitAction(state.game_id, action);
  }, [state]);

  const reset = useCallback(() => {
    window.history.replaceState({}, '', '/wolf/');
    dispatch({ type: 'RESET' });
  }, []);

  const dismissGameOver = useCallback(() => {
    dispatch({ type: 'DISMISS_GAME_OVER' });
  }, []);

  const loginAction = useCallback((userId: number, username: string, token: string) => {
    dispatch({ type: 'LOGIN', payload: { user_id: userId, username, token } });
  }, []);

  const logoutAction = useCallback(() => {
    dispatch({ type: 'LOGOUT' });
  }, []);

  return (
    <GameContext.Provider value={{ state, startGame, sendAction, updateState, reset, dismissGameOver, loginAction, logoutAction }}>
      {children}
    </GameContext.Provider>
  );
}

export function useGame(): ContextValue {
  const ctx = useContext(GameContext);
  if (!ctx) throw new Error('useGame must be used within GameProvider');
  return ctx;
}