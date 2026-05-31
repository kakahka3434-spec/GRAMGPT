import React, { useState } from 'react';
import { X, Rocket, Search, GraduationCap, HandSparkles, Flame, Users, ChartLine, Heart, DollarSign, Sliders, Brain, Plus } from 'lucide-react';

/* =====================================================
   TeleBoost AI — Campaign Creation Modal
   React + Tailwind CSS
   ===================================================== */

type Goal = 'leads' | 'traffic' | 'engagement' | 'sales';
type TemplateKey = 'expert' | 'supportive' | 'persuasive';

interface Template {
  key: TemplateKey;
  label: string;
  description: string;
  icon: React.ReactNode;
  prompt: string;
}

const TEMPLATES: Template[] = [
  {
    key: 'expert',
    label: 'Экспертный',
    description: 'Цифры, факты, аргументы',
    icon: <GraduationCap className="w-5 h-5" />,
    prompt:
      'Ты — эксперт в нише. Пиши развёрнутые, аргументированные комментарии с цифрами и фактами. Стиль: уверенный, профессиональный. Цель: показать глубокую экспертизу и вызвать доверие.',
  },
  {
    key: 'supportive',
    label: 'Поддерживающий',
    description: 'Тёплый, эмпатичный тон',
    icon: <HandSparkles className="w-5 h-5" />,
    prompt:
      'Ты — дружелюбный помощник. Отвечай тепло, поддерживающе, задавай уточняющие вопросы. Стиль: мягкий, эмпатичный. Цель: установить контакт и продолжить диалог.',
  },
  {
    key: 'persuasive',
    label: 'Продающий',
    description: 'Боль → решение → CTA',
    icon: <Flame className="w-5 h-5" />,
    prompt:
      'Ты — продавец-консультант. Структурируй ответ как мини-продажу: боль → решение → призыв. Стиль: энергичный, убедительный. Цель: конверсия в личное сообщение.',
  },
];

const GOALS: { key: Goal; label: string; icon: React.ReactNode }[] = [
  { key: 'leads', label: 'Лиды', icon: <Users className="w-3.5 h-3.5" /> },
  { key: 'traffic', label: 'Трафик', icon: <ChartLine className="w-3.5 h-3.5" /> },
  { key: 'engagement', label: 'Вовлеч.', icon: <Heart className="w-3.5 h-3.5" /> },
  { key: 'sales', label: 'Продажи', icon: <DollarSign className="w-3.5 h-3.5" /> },
];

// ==================== Component ====================

interface CampaignModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (data: {
    name: string;
    goal: Goal;
    budget: number;
    channels: string[];
    prompt: string;
  }) => Promise<void>;
}

export default function CampaignCreationModal({ isOpen, onClose, onCreate }: CampaignModalProps) {
  const [activeTab, setActiveTab] = useState<'config' | 'prompt' | 'parsing'>('config');
  const [name, setName] = useState('Новая кампания');
  const [goal, setGoal] = useState<Goal>('leads');
  const [budget, setBudget] = useState(200);
  const [channels, setChannels] = useState('');
  const [prompt, setPrompt] = useState('');
  const [parseKeywords, setParseKeywords] = useState('');
  const [parseCount, setParseCount] = useState(500);
  const [activeTemplate, setActiveTemplate] = useState<TemplateKey | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const applyTemplate = (t: Template) => {
    setActiveTemplate(t.key);
    setPrompt(t.prompt);
  };

  const handleCreate = async () => {
    setLoading(true);
    try {
      await onCreate({
        name,
        goal,
        budget,
        channels: channels
          .split('\n')
          .map((s) => s.trim())
          .filter(Boolean),
        prompt,
      });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-lg bg-[#0C0F23] border border-white/10 rounded-2xl shadow-2xl animate-in">
        {/* Header */}
        <div className="p-5 pb-3">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Brain className="w-5 h-5 text-cyan-400" />
              Новая кампания
            </h3>
            <button
              onClick={onClose}
              className="w-7 h-7 rounded-full bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white flex items-center justify-center transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-sm text-gray-400">ИИ настроит стратегию продвижения под вашу цель</p>
        </div>

        {/* Tabs */}
        <div className="flex mx-5 border-b border-white/10">
          {[
            { key: 'config' as const, label: 'Настройки', icon: <Sliders className="w-3.5 h-3.5" /> },
            { key: 'prompt' as const, label: 'AI Промпт', icon: <Brain className="w-3.5 h-3.5" /> },
            { key: 'parsing' as const, label: 'Парсинг', icon: <Search className="w-3.5 h-3.5" /> },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 py-3 text-xs font-semibold flex items-center justify-center gap-1.5 border-b-2 transition-colors relative ${
                activeTab === tab.key
                  ? 'text-cyan-400 border-cyan-400'
                  : 'text-gray-500 border-transparent hover:text-gray-300'
              }`}
            >
              {tab.icon}
              {tab.label}
              {tab.key === 'parsing' && (
                <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 bg-[#0C0F23] border border-white/10 text-gray-400 text-[10px] px-2 py-0.5 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                  Ищите каналы прямо здесь
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab: Config */}
        {activeTab === 'config' && (
          <div className="p-5 space-y-4">
            <div>
              <label className="block text-xs text-gray-300 font-medium mb-1.5">Название кампании</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[#1A1D2E] border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition-colors"
                placeholder="Например: Крипта-февраль 2026"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-300 font-medium mb-1.5">Цель кампании</label>
              <div className="grid grid-cols-4 gap-2">
                {GOALS.map((g) => (
                  <button
                    key={g.key}
                    onClick={() => setGoal(g.key)}
                    className={`flex flex-col items-center gap-1 py-2.5 px-2 rounded-lg border text-xs font-semibold transition-all ${
                      goal === g.key
                        ? 'border-cyan-400 bg-cyan-400/10 text-cyan-400'
                        : 'border-white/10 text-gray-400 hover:text-gray-200 hover:border-gray-600'
                    }`}
                  >
                    {g.icon}
                    {g.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-300 font-medium mb-1.5">Бюджет на аккаунт (USDT)</label>
              <input
                type="number"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 bg-[#1A1D2E] border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-300 font-medium mb-1.5">
                Целевые каналы (по одному на строку)
              </label>
              <textarea
                value={channels}
                onChange={(e) => setChannels(e.target.value)}
                rows={3}
                className="w-full px-3.5 py-2.5 bg-[#1A1D2E] border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition-colors resize-none"
                placeholder="@channel1\n@channel2"
              />
              <p className="text-[10px] text-gray-500 mt-1.5 flex items-center gap-1">
                Можно оставить пустым — ИИ подберёт каналы сам
              </p>
            </div>
          </div>
        )}

        {/* Tab: AI Prompt */}
        {activeTab === 'prompt' && (
          <div className="p-5 space-y-4">
            <div>
              <label className="block text-xs text-gray-300 font-medium mb-2">Шаблоны промптов</label>
              <div className="grid grid-cols-3 gap-2">
                {TEMPLATES.map((t) => (
                  <button
                    key={t.key}
                    onClick={() => applyTemplate(t)}
                    className={`p-3 rounded-xl border text-center transition-all ${
                      activeTemplate === t.key
                        ? 'border-cyan-400 bg-cyan-400/10 text-white'
                        : 'border-white/10 text-gray-400 hover:border-gray-600 hover:text-gray-200 hover:-translate-y-0.5'
                    }`}
                  >
                    <div className="flex justify-center mb-1.5 text-cyan-400">{t.icon}</div>
                    <div className="text-xs font-bold mb-0.5">{t.label}</div>
                    <div className="text-[10px] text-gray-500">{t.description}</div>
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-300 font-medium mb-1.5">AI Промпт</label>
              <textarea
                value={prompt}
                onChange={(e) => {
                  setPrompt(e.target.value);
                  setActiveTemplate(null);
                }}
                rows={6}
                className="w-full px-3.5 py-2.5 bg-[#1A1D2E] border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition-colors resize-none"
                placeholder="Опишите стиль и тон комментариев..."
              />
              <p className="text-[10px] text-gray-500 mt-1.5 flex items-center gap-1">
                Чем детальнее промпт — тем естественнее комментарии
              </p>
            </div>
          </div>
        )}

        {/* Tab: Parsing */}
        {activeTab === 'parsing' && (
          <div className="p-5 space-y-4 text-center">
            <div className="w-12 h-12 mx-auto rounded-xl bg-cyan-400/10 border border-white/10 flex items-center justify-center text-cyan-400">
              <Search className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-semibold text-white">Парсинг каналов</h4>
            <p className="text-xs text-gray-400">Настройте источник аудитории для кампании</p>
            <div className="text-left space-y-4">
              <div>
                <label className="block text-xs text-gray-300 font-medium mb-1.5">Ключевые слова для поиска</label>
                <input
                  value={parseKeywords}
                  onChange={(e) => setParseKeywords(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#1A1D2E] border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition-colors"
                  placeholder="крипта, инвестиции, трейдинг"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-300 font-medium mb-1.5">Количество участников для сбора</label>
                <input
                  type="number"
                  value={parseCount}
                  onChange={(e) => setParseCount(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 bg-[#1A1D2E] border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-300 font-medium mb-1.5">Глубина парсинга</label>
                <div className="grid grid-cols-3 gap-2">
                  {['Поверхностный', 'Средний', 'Глубокий'].map((label) => (
                    <button
                      key={label}
                      className="py-2 rounded-lg border border-white/10 text-xs font-semibold text-gray-400 hover:text-gray-200 hover:border-gray-600 transition-all"
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex gap-3 p-5 pt-4 border-t border-white/10">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-lg border border-white/10 text-sm font-semibold text-gray-300 hover:text-white hover:border-gray-600 transition-all flex items-center justify-center gap-2"
          >
            <X className="w-3.5 h-3.5" />
            Отмена
          </button>
          <button
            onClick={handleCreate}
            disabled={loading}
            className="flex-[2] py-2.5 rounded-lg text-sm font-bold text-[#05050A] flex items-center justify-center gap-2 transition-all bg-gradient-to-r from-cyan-400 to-cyan-500 hover:shadow-[0_0_32px_rgba(0,229,255,0.3)] hover:-translate-y-0.5 active:scale-[0.97] disabled:opacity-50"
          >
            <Rocket className="w-4 h-4" />
            {loading ? 'Запуск...' : 'Запустить кампанию'}
          </button>
        </div>
      </div>
    </div>
  );
}
