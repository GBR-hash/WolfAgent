import { useState } from 'react';
import { useGame } from '../context/GameContext';
import { login, register } from '../api/client';

interface AuthModalProps {
  onClose: () => void;
}

export function AuthModal({ onClose }: AuthModalProps) {
  const { state, loginAction } = useGame();
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('请填写用户名和密码');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const fn = tab === 'login' ? login : register;
      const result = await fn(username.trim(), password.trim());
      loginAction(result.user_id, result.username, result.token);
      onClose();
    } catch (e: any) {
      setError(e.message || '操作失败');
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-night-card border border-night-border rounded-2xl p-6 w-full max-w-sm mx-4 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex mb-4 bg-night rounded-lg p-1">
          <button
            className={'flex-1 py-2 rounded-md text-sm font-medium transition-colors ' +
              (tab === 'login' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-gray-200')}
            onClick={() => { setTab('login'); setError(''); }}
          >
            登录
          </button>
          <button
            className={'flex-1 py-2 rounded-md text-sm font-medium transition-colors ' +
              (tab === 'register' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-gray-200')}
            onClick={() => { setTab('register'); setError(''); }}
          >
            注册
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="space-y-3">
            <input
              className="w-full bg-night border border-night-border rounded-lg px-3 py-2.5 text-gray-200 text-sm focus:outline-none focus:border-purple-500"
              placeholder="用户名"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoFocus
            />
            <input
              className="w-full bg-night border border-night-border rounded-lg px-3 py-2.5 text-gray-200 text-sm focus:outline-none focus:border-purple-500"
              type="password"
              placeholder="密码"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
            {error && <p className="text-red-400 text-xs">{error}</p>}
            <button
              className="w-full bg-purple-600 hover:bg-purple-500 text-white rounded-lg py-2.5 text-sm font-medium transition-colors disabled:opacity-50"
              type="submit"
              disabled={loading}
            >
              {loading ? '处理中...' : (tab === 'login' ? '登录' : '注册')}
            </button>
          </div>
        </form>

        <button
          className="w-full mt-3 text-gray-500 hover:text-gray-300 text-xs transition-colors"
          onClick={onClose}
        >
          取消
        </button>
      </div>
    </div>
  );
}
