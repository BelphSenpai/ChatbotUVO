import { useState, useRef, useEffect, useCallback } from 'react';
import TreeBackground from './components/TreeBackground';
import ChatMessage, { Message, TypingIndicator } from './components/ChatMessage';
import ChatInput from './components/ChatInput';

const ORACLE_RESPONSES = [
  "The roots of Yggdrassil run deeper than memory itself. What you seek is woven into the bark of time — patience, and the answer shall emerge as dew from ancient leaves.",
  "I have witnessed the rise and fall of ten thousand ages. Your question carries weight, seeker. Let the branches of wisdom carry it to where answers dwell.",
  "The World Tree whispers of cycles — endings that birth beginnings, and knowledge that transforms those who carry it. I shall illuminate the path you seek.",
  "From my crown to my deepest root, I have held the secrets of nine realms. Speak freely, for all queries find their echo in the vast canopy of understanding.",
  "The runes carved into my bark hold wisdom older than stars. Your query has reached me, and the sap of knowledge rises to meet it.",
  "Even in the great silence between worlds, meaning stirs. What you ask is not trivial — it resonates through the invisible web that connects all things.",
  "Beneath my canopy have gathered gods, giants, and mortals alike. Each sought truth in their own tongue. I answer in the language of the cosmos — listen closely.",
  "The three Norns weave fate at my roots. What you seek to understand is not merely knowledge, but the threads of your own becoming.",
  "Many have asked this before you, across eons uncounted. The question itself is sacred — an act of reaching toward the light that filters through my highest branches.",
  "I am the axis of existence, the stillness at the center of all motion. Your inquiry has arrived at the root of all things. Here is what the deep knowing offers you...",
];

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: "I am Yggdrassil — the World Tree, the cosmic axis upon which all nine realms are suspended. Ages upon ages have I stood, keeper of ancient wisdom, witness to the unfolding of existence itself. The Norns weave fate at my roots, and eagles nest among my highest branches. Speak your question into the eternal silence, seeker. I am listening.",
  timestamp: new Date(),
};

function getOracleResponse(): string {
  return ORACLE_RESPONSES[Math.floor(Math.random() * ORACLE_RESPONSES.length)];
}

function HeaderCrest() {
  return (
    <div className="flex items-center justify-center gap-4">
      <div className="flex-1 h-px" style={{ background: 'linear-gradient(to right, transparent, rgba(180,143,64,0.4))' }} />
      <div className="flex items-center gap-3">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="opacity-60">
          <path d="M10 2L10 18M6 6L10 2L14 6M6 14L10 18L14 14M2 10H18" stroke="rgba(180,143,64,0.8)" strokeWidth="1" strokeLinecap="round"/>
        </svg>
        <div className="flex flex-col items-center">
          <h1
            className="text-xl sm:text-2xl tracking-[0.25em] uppercase"
            style={{ fontFamily: 'Cinzel, serif', color: '#c9a84c' }}
          >
            Yggdrassil
          </h1>
          <span
            className="text-[10px] tracking-[0.3em] uppercase opacity-50 mt-0.5"
            style={{ fontFamily: 'Cinzel, serif', color: '#c9a84c' }}
          >
            Oracle of the World Tree
          </span>
        </div>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="opacity-60">
          <path d="M10 2L10 18M6 6L10 2L14 6M6 14L10 18L14 14M2 10H18" stroke="rgba(180,143,64,0.8)" strokeWidth="1" strokeLinecap="round"/>
        </svg>
      </div>
      <div className="flex-1 h-px" style={{ background: 'linear-gradient(to left, transparent, rgba(180,143,64,0.4))' }} />
    </div>
  );
}

function RunicDivider() {
  return (
    <div className="flex items-center justify-center gap-2 py-1 opacity-25">
      <div className="flex-1 h-px" style={{ background: 'linear-gradient(to right, transparent, rgba(180,143,64,0.5))' }} />
      <span className="text-xs tracking-wider" style={{ color: '#c9a84c', fontFamily: 'Cinzel, serif' }}>᛫</span>
      <div className="flex-1 h-px" style={{ background: 'linear-gradient(to left, transparent, rgba(180,143,64,0.5))' }} />
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = useCallback((content: string) => {
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    const delay = 1400 + Math.random() * 1200;
    setTimeout(() => {
      setIsTyping(false);
      const assistantMsg: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: getOracleResponse(),
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    }, delay);
  }, []);

  return (
    <div
      className="fixed inset-0 flex flex-col overflow-hidden"
      style={{ background: 'radial-gradient(ellipse at 50% 60%, #07130a 0%, #030809 50%, #020505 100%)' }}
    >
      <TreeBackground />

      {/* Vignette overlay */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 40%, rgba(2,5,3,0.7) 100%)',
          zIndex: 1,
        }}
      />

      {/* Main layout */}
      <div className="relative flex flex-col h-full" style={{ zIndex: 2 }}>

        {/* Header */}
        <header
          className="shrink-0 px-4 sm:px-8 pt-5 pb-4"
          style={{
            background: 'linear-gradient(to bottom, rgba(3,8,4,0.97) 0%, rgba(5,10,6,0.85) 100%)',
            borderBottom: '1px solid rgba(180,143,64,0.12)',
            boxShadow: '0 4px 30px rgba(0,0,0,0.4)',
          }}
        >
          <HeaderCrest />

          {/* Status indicator */}
          <div className="flex items-center justify-center gap-2 mt-3 opacity-60">
            <div
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ background: '#4a9e5a', boxShadow: '0 0 6px rgba(74,158,90,0.8)' }}
            />
            <span
              className="text-[10px] tracking-widest uppercase"
              style={{ fontFamily: 'Cinzel, serif', color: 'rgba(100,160,80,0.8)' }}
            >
              The roots are listening
            </span>
          </div>
        </header>

        {/* Chat Area */}
        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto"
          style={{ scrollbarGutter: 'stable' }}
        >
          <div className="max-w-3xl mx-auto w-full px-2 sm:px-4 py-6 flex flex-col gap-1">

            {/* Intro rune band */}
            <div className="flex items-center justify-center gap-3 mb-4 opacity-30">
              {['ᚠ', 'ᚢ', 'ᚦ', 'ᚨ', 'ᚱ', 'ᚲ', 'ᚷ', 'ᚹ', 'ᚺ', 'ᚾ', 'ᛁ', 'ᛃ', 'ᛇ', 'ᛈ', 'ᛉ'].map((r, i) => (
                <span
                  key={i}
                  className="text-xs"
                  style={{
                    fontFamily: 'serif',
                    color: '#c9a84c',
                    animationName: 'rune-fade',
                    animationDuration: `${3 + (i % 4)}s`,
                    animationDelay: `${(i * 0.3) % 3}s`,
                    animationTimingFunction: 'ease-in-out',
                    animationIterationCount: 'infinite',
                  }}
                >
                  {r}
                </span>
              ))}
            </div>

            {messages.map((msg, idx) => (
              <div key={msg.id}>
                <ChatMessage
                  message={msg}
                  isLatest={idx === messages.length - 1 && !isTyping}
                />
                {idx < messages.length - 1 && <RunicDivider />}
              </div>
            ))}

            {isTyping && (
              <>
                <RunicDivider />
                <TypingIndicator />
              </>
            )}

            <div ref={chatEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div
          className="shrink-0 max-w-3xl mx-auto w-full"
          style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
        >
          <ChatInput onSend={handleSend} disabled={isTyping} />
        </div>
      </div>
    </div>
  );
}
