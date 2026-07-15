import { useState, useMemo } from 'react';
import { useGame } from '../context/GameContext';
import { AuthModal } from './AuthModal';

interface ParticleData {
  width: number;
  height: number;
  left: string;
  top: string;
  duration: string;
  delay: string;
  colorClass: string;
}

interface SparkData {
  left: string;
  top: string;
  delay: string;
  size: string;
}

// Generate deterministic particle data (outside render to avoid hydration mismatch)
function generateParticles(): ParticleData[] {
  const colors = [
    'bg-purple-400/50',
    'bg-purple-300/40',
    'bg-purple-400/35',
    'bg-blue-400/30',
    'bg-purple-500/45',
    'bg-violet-400/35',
    'bg-purple-300/30',
    'bg-blue-300/25',
  ];
  const particles: ParticleData[] = [];
  for (let i = 0; i < 80; i++) {
    const seed = (i * 137.508) % 360;
    const sizeBase = 3 + (i % 4) * 3 + Math.sin(seed) * 4;
    particles.push({
      width: Math.max(2, sizeBase + Math.sin(i * 2.7) * 2),
      height: Math.max(2, sizeBase + Math.cos(i * 3.1) * 2),
      left: ((i * 67 + 23) % 100) + '%',
      top: ((i * 89 + 41) % 100) + '%',
      duration: (8 + (i % 14)) + 's',
      delay: ((i * 3.7) % 8) + 's',
      colorClass: colors[i % colors.length],
    });
  }
  return particles;
}

function generateSparks(): SparkData[] {
  const sparks: SparkData[] = [];
  for (let i = 0; i < 12; i++) {
    sparks.push({
      left: (25 + (i * 53 + 17) % 50) + '%',
      top: (20 + (i * 41 + 13) % 60) + '%',
      delay: ((i * 2.3) % 6) + 's',
      size: (i % 3 === 0 ? 'w-1.5 h-1.5' : 'w-1 h-1'),
    });
  }
  return sparks;
}

const PARTICLES = generateParticles();
const SPARKS = generateSparks();

export function HomePage() {
  const { startGame, state } = useGame();
  const [showAuth, setShowAuth] = useState(false);
  const [starting, setStarting] = useState(false);
  const [selectedRole, setSelectedRole] = useState('random');
  const [playStyle, setPlayStyle] = useState('balanced');

  const ROLES = [
    { value: 'random', label: '🎲 随机' },
    { value: 'werewolf', label: '🐺 狼人' },
    { value: 'witch', label: '🧪 女巫' },
    { value: 'seer', label: '🔮 预言家' },
    { value: 'villager', label: '💑 村民' },
  ];

  const handleStart = async () => {
    setStarting(true);
    try {
      const result = await startGame(selectedRole, playStyle);
      // URL is now managed by GameContext.startGame
    } catch (e) {
      console.error(e);
    }
    setStarting(false);
  };

  const user = state?.user;

  return (
    <div className="relative flex flex-col items-center justify-center h-screen w-screen overflow-hidden bg-night">
      {/* Layer 1: Central radial glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute rounded-full bg-purple-600/8"
          style={{
            width: '700px',
            height: '700px',
            left: '50%',
            top: '42%',
            transform: 'translate(-50%, -50%)',
            filter: 'blur(120px)',
          }}
        />
        <div
          className="absolute rounded-full bg-purple-400/6"
          style={{
            width: '500px',
            height: '500px',
            left: '50%',
            top: '42%',
            transform: 'translate(-50%, -50%)',
            filter: 'blur(80px)',
          }}
        />
        <div
          className="absolute rounded-full bg-blue-500/4"
          style={{
            width: '400px',
            height: '400px',
            left: '50%',
            top: '45%',
            transform: 'translate(-50%, -50%)',
            filter: 'blur(100px)',
          }}
        />
      </div>

      {/* Layer 2: Floating particles */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {PARTICLES.map((p, i) => (
          <div
            key={i}
            className={'absolute rounded-full ' + p.colorClass}
            style={{
              width: p.width + 'px',
              height: p.height + 'px',
              left: p.left,
              top: p.top,
              animation: 'particleFloat ' + p.duration + ' ease-in-out infinite',
              animationDelay: p.delay,
              boxShadow: '0 0 ' + (p.width * 2) + 'px ' + (p.width * 0.8) + 'px currentColor',
            }}
          />
        ))}
      </div>

      {/* Layer 3: Sparkle dots */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {SPARKS.map((s, i) => (
          <div
            key={'spark' + i}
            className={'absolute rounded-full bg-white/60 ' + s.size}
            style={{
              left: s.left,
              top: s.top,
              animation: 'sparkPulse 3s ease-in-out infinite',
              animationDelay: s.delay,
            }}
          />
        ))}
      </div>

      {/* Content */}
      <div className="relative z-10 text-center max-w-lg px-6">
        <div
          className="text-8xl mb-6 animate-fade-in select-none"
          style={{
            animationDelay: '0.1s',
            filter: 'drop-shadow(0 0 40px rgba(168,85,247,0.5)) drop-shadow(0 0 80px rgba(168,85,247,0.2))',
          }}
        >
          🐺
        </div>

        <h1
          className="text-5xl font-bold text-purple-300 mb-4 animate-fade-in select-none"
          style={{
            animationDelay: '0.3s',
            textShadow: '0 0 40px rgba(168,85,247,0.4), 0 0 80px rgba(168,85,247,0.15)',
          }}
        >
          WolfAgent
        </h1>

        <p className="text-gray-400 text-lg mb-2 animate-fade-in" style={{ animationDelay: '0.6s' }}>
          已为你匹配到实力相当的 AI 对手和 AI 队友
        </p>
        <p className="text-gray-500 text-base mb-8 animate-fade-in" style={{ animationDelay: '0.9s' }}>
          开始你的博弈之旅吧
        </p>

        {/* Play style selector */}
        <div className="mb-4 animate-fade-in" style={{ animationDelay: '1.05s' }}>
          <label className="text-gray-500 text-xs mb-2 block">游戏风格</label>
          <div className="flex justify-center gap-2">
            {[
              { value: 'aggressive', label: '⚡ 激进', desc: '频繁跳身份对抗' },
              { value: 'balanced', label: '⚖ 均衡', desc: '策略灵活多变' },
              { value: 'conservative', label: '🛡 保守', desc: '纯逻辑推理' },
            ].map(s => (
              <button
                key={s.value}
                className={'flex flex-col items-center px-3 py-2 rounded-lg text-sm font-medium transition-all ' +
                  (playStyle === s.value
                    ? 'bg-amber-600 text-white shadow-lg shadow-amber-600/30'
                    : 'bg-night-card border border-night-border text-gray-400 hover:border-amber-500/40')}
                onClick={() => setPlayStyle(s.value)}
              >
                <span>{s.label}</span>
                <span className="text-[10px] opacity-60 mt-0.5">{s.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Role selector */}
        <div className="mb-4 animate-fade-in" style={{ animationDelay: '1.1s' }}>
          <label className="text-gray-500 text-xs mb-2 block">身份偏好 (可选)</label>
          <div className="flex flex-wrap justify-center gap-2">
            {ROLES.map(r => (
              <button
                key={r.value}
                className={'px-3 py-1.5 rounded-lg text-sm font-medium transition-all ' +
                  (selectedRole === r.value
                    ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
                    : 'bg-night-card border border-night-border text-gray-400 hover:border-purple-500/40')}
                onClick={() => setSelectedRole(r.value)}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-3 justify-center animate-fade-in" style={{ animationDelay: '1.3s' }}>
          <button
            className="bg-purple-600 hover:bg-purple-500 text-white rounded-xl px-8 py-3 text-base font-medium transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg shadow-purple-600/25 disabled:opacity-50"
            onClick={handleStart}
            disabled={starting}
          >
            🎮 {starting ? '创建中...' : '直接开始'}
          </button>
          {!user && (
            <button
              className="bg-gray-700/50 hover:bg-gray-700/80 border border-gray-600/30 text-gray-300 rounded-xl px-6 py-3 text-base font-medium transition-all duration-200 hover:scale-105 active:scale-95"
              onClick={() => setShowAuth(true)}
            >
              💑 登录 / 注册
            </button>
          )}
          {user && (
            <div className="text-gray-400 text-sm flex items-center gap-2">
              💑 欢迎, {user.username}
            </div>
          )}
        </div>

        {!user && (
          <p className="text-gray-600 text-xs mt-4 animate-fade-in" style={{ animationDelay: '1.5s' }}>
            匿名游玩不保存记录，登录后可归档游戏历程
          </p>
        )}
      </div>

      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}

      <style>{`
        @keyframes particleFloat {
          0%, 100% {
            transform: translateY(0) translateX(0) scale(1);
          }
          15% {
            transform: translateY(-50px) translateX(25px) scale(1.3);
          }
          35% {
            transform: translateY(-20px) translateX(-20px) scale(0.85);
          }
          55% {
            transform: translateY(-70px) translateX(-30px) scale(1.2);
          }
          75% {
            transform: translateY(-10px) translateX(15px) scale(0.9);
          }
        }

        @keyframes sparkPulse {
          0%, 100% {
            opacity: 0.2;
            transform: scale(0.8);
          }
          50% {
            opacity: 0.9;
            transform: scale(1.8);
            box-shadow: 0 0 6px 2px rgba(255,255,255,0.3);
          }
        }
      `}</style>
    </div>
  );
}
