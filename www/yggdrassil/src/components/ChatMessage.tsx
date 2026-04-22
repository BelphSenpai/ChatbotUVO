import { useEffect, useRef } from 'react';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
  isLatest: boolean;
}

const RuneSymbol = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="opacity-60 shrink-0">
    <path d="M8 1L8 15M4 4L8 1L12 4M4 12L8 15L12 12M3 8H13" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
  </svg>
);

const OracleIcon = () => (
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" className="shrink-0">
    <circle cx="16" cy="16" r="14" stroke="rgba(180,143,64,0.5)" strokeWidth="1"/>
    <circle cx="16" cy="16" r="10" stroke="rgba(180,143,64,0.3)" strokeWidth="0.5"/>
    <path d="M16 4L16 28M4 16L28 16" stroke="rgba(180,143,64,0.3)" strokeWidth="0.5"/>
    <path d="M8 8L24 24M24 8L8 24" stroke="rgba(180,143,64,0.2)" strokeWidth="0.5"/>
    <circle cx="16" cy="16" r="4" fill="rgba(180,143,64,0.2)" stroke="rgba(180,143,64,0.8)" strokeWidth="1"/>
    <circle cx="16" cy="16" r="1.5" fill="rgba(200,170,80,0.9)"/>
  </svg>
);

const UserIcon = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none" className="shrink-0">
    <circle cx="14" cy="14" r="12" stroke="rgba(120,160,100,0.4)" strokeWidth="1"/>
    <circle cx="14" cy="10" r="4" stroke="rgba(120,160,100,0.6)" strokeWidth="1" fill="rgba(120,160,100,0.1)"/>
    <path d="M5 24c0-5 4-8 9-8s9 3 9 8" stroke="rgba(120,160,100,0.6)" strokeWidth="1" fill="none"/>
  </svg>
);

export default function ChatMessage({ message, isLatest }: ChatMessageProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isLatest && ref.current) {
      ref.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [isLatest]);

  const isAssistant = message.role === 'assistant';

  const formatTime = (d: Date) =>
    d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (isAssistant) {
    return (
      <div ref={ref} className="message-enter flex gap-4 px-4 py-2 group">
        <div className="mt-1">
          <OracleIcon />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <span
              className="text-xs tracking-widest uppercase"
              style={{ fontFamily: 'Cinzel, serif', color: 'rgba(180,143,64,0.8)' }}
            >
              Yggdrassil
            </span>
            <span className="flex-1 h-px" style={{ background: 'linear-gradient(to right, rgba(180,143,64,0.3), transparent)' }} />
            <span className="text-xs opacity-30" style={{ fontFamily: 'Inter, sans-serif', color: '#c9a84c' }}>
              {formatTime(message.timestamp)}
            </span>
          </div>

          <div
            className="relative rounded-2xl rounded-tl-sm p-5 leading-relaxed"
            style={{
              background: 'linear-gradient(135deg, rgba(12, 28, 14, 0.85) 0%, rgba(8, 18, 10, 0.9) 100%)',
              border: '1px solid rgba(180, 143, 64, 0.2)',
              boxShadow: '0 0 30px rgba(180, 143, 64, 0.05), inset 0 1px 0 rgba(180, 143, 64, 0.1)',
              fontFamily: 'Crimson Text, serif',
              fontSize: '1.05rem',
              color: '#e8dfc8',
            }}
          >
            {/* Corner rune ornaments */}
            <span className="absolute top-2 left-2 text-[10px] opacity-20" style={{ color: '#c9a84c' }}>᚛</span>
            <span className="absolute top-2 right-2 text-[10px] opacity-20" style={{ color: '#c9a84c' }}>᚜</span>

            <p style={{ lineHeight: '1.75' }}>{message.content}</p>

            {/* Bottom shimmer accent */}
            <div
              className="absolute bottom-0 left-4 right-4 h-px rounded-full"
              style={{ background: 'linear-gradient(to right, transparent, rgba(180,143,64,0.3), transparent)' }}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div ref={ref} className="message-enter flex gap-4 px-4 py-2 justify-end group">
      <div className="flex-1 min-w-0 flex flex-col items-end">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-xs opacity-30" style={{ fontFamily: 'Inter, sans-serif', color: '#9ab890' }}>
            {formatTime(message.timestamp)}
          </span>
          <span
            className="flex gap-1 items-center text-xs tracking-widest uppercase"
            style={{ fontFamily: 'Cinzel, serif', color: 'rgba(120,160,100,0.7)' }}
          >
            <RuneSymbol />
            Seeker
          </span>
        </div>

        <div
          className="max-w-lg rounded-2xl rounded-tr-sm px-5 py-4 leading-relaxed"
          style={{
            background: 'linear-gradient(135deg, rgba(20, 45, 25, 0.6) 0%, rgba(15, 35, 18, 0.7) 100%)',
            border: '1px solid rgba(120, 160, 100, 0.2)',
            boxShadow: '0 0 20px rgba(80, 140, 60, 0.05)',
            fontFamily: 'Inter, sans-serif',
            fontSize: '0.92rem',
            color: '#d4e8cc',
          }}
        >
          {message.content}
        </div>
      </div>
      <div className="mt-1">
        <UserIcon />
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="message-enter flex gap-4 px-4 py-2">
      <div className="mt-1">
        <OracleIcon />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-3 mb-2">
          <span
            className="text-xs tracking-widest uppercase"
            style={{ fontFamily: 'Cinzel, serif', color: 'rgba(180,143,64,0.8)' }}
          >
            Yggdrassil
          </span>
          <span className="flex-1 h-px" style={{ background: 'linear-gradient(to right, rgba(180,143,64,0.3), transparent)' }} />
        </div>
        <div
          className="inline-flex items-center gap-2 rounded-2xl rounded-tl-sm px-5 py-4"
          style={{
            background: 'linear-gradient(135deg, rgba(12, 28, 14, 0.85) 0%, rgba(8, 18, 10, 0.9) 100%)',
            border: '1px solid rgba(180, 143, 64, 0.2)',
          }}
        >
          <span className="text-xs opacity-50 mr-1" style={{ fontFamily: 'Cinzel, serif', color: '#c9a84c' }}>
            Consulting the roots
          </span>
          {[0, 1, 2].map(i => (
            <span
              key={i}
              className="typing-dot inline-block w-1.5 h-1.5 rounded-full"
              style={{
                background: '#c9a84c',
                animationDelay: `${i * 0.2}s`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
