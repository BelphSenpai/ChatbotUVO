import { useEffect, useMemo, useRef, useState } from 'react';
import TreeBackground from './components/TreeBackground';
import ChatMessage, { Message, TypingIndicator } from './components/ChatMessage';
import ChatInput from './components/ChatInput';

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: "I am Yggdrassil — the World Tree, the cosmic axis upon which all nine realms are suspended. Ages upon ages have I stood, keeper of ancient wisdom, witness to the unfolding of existence itself. The Norns weave fate at my roots, and eagles nest among my highest branches. Speak your question into the eternal silence, seeker. I am listening.",
  timestamp: new Date(),
};

interface SessionInfo {
  usuario?: string;
  rol?: string;
}

interface StoredMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

function storageKeyForUser(usuario: string) {
  return `conversacion_yggdrassil_${usuario.toLowerCase()}`;
}

function parseStoredMessages(raw: string | null): Message[] | null {
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as StoredMessage[];
    if (!Array.isArray(parsed) || parsed.length === 0) {
      return null;
    }

    return parsed.map(message => ({
      ...message,
      timestamp: new Date(message.timestamp),
    }));
  } catch {
    return null;
  }
}

function serializeMessages(messages: Message[]): StoredMessage[] {
  return messages.map(message => ({
    ...message,
    timestamp: message.timestamp.toISOString(),
  }));
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

function Navbar({
  isAdmin,
  availableIAs,
}: {
  isAdmin: boolean;
  availableIAs: string[];
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const closeMenu = () => setMenuOpen(false);
    document.addEventListener('click', closeMenu);
    return () => document.removeEventListener('click', closeMenu);
  }, []);

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-20 px-4 sm:px-6"
      style={{
        background: 'linear-gradient(to bottom, rgba(4, 9, 5, 0.95) 0%, rgba(6, 12, 7, 0.84) 100%)',
        borderBottom: '1px solid rgba(180,143,64,0.16)',
        boxShadow: '0 8px 28px rgba(0,0,0,0.28)',
        backdropFilter: 'blur(10px)',
      }}
    >
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-center gap-3 sm:gap-6 text-[11px] uppercase tracking-[0.22em] sm:text-xs">
        <a className="opacity-60 transition-opacity hover:opacity-100" href="/ficha" style={{ color: '#d4c49a' }}>
          Ficha
        </a>
        <a className="opacity-60 transition-opacity hover:opacity-100" href="/tramas" style={{ color: '#d4c49a' }}>
          Tramas
        </a>
        <a className="opacity-60 transition-opacity hover:opacity-100" href="/poderes" style={{ color: '#d4c49a' }}>
          Poderes
        </a>
        <a
          className="border-b pb-1 opacity-100"
          href="/yggdrassil"
          style={{
            color: '#c9a84c',
            borderColor: 'rgba(201,168,76,0.8)',
            textShadow: '0 0 10px rgba(201,168,76,0.35)',
          }}
        >
          Yggdrassil
        </a>
        {isAdmin ? (
          <a className="opacity-60 transition-opacity hover:opacity-100" href="/admin" style={{ color: '#d4c49a' }}>
            Admin
          </a>
        ) : null}
        {availableIAs.length > 0 ? (
          <div className="relative">
            <button
              type="button"
              className="opacity-60 transition-opacity hover:opacity-100"
              onClick={event => {
                event.stopPropagation();
                setMenuOpen(open => !open);
              }}
              style={{ color: '#d4c49a' }}
            >
              IAs {menuOpen ? '▴' : '▾'}
            </button>
            {menuOpen ? (
              <div
                className="absolute right-0 top-9 min-w-40 rounded-xl p-2"
                onClick={event => event.stopPropagation()}
                style={{
                  background: 'rgba(10, 18, 11, 0.96)',
                  border: '1px solid rgba(180,143,64,0.18)',
                  boxShadow: '0 10px 30px rgba(0,0,0,0.35)',
                }}
              >
                {availableIAs.map(ia => (
                  <a
                    key={ia}
                    className="block rounded-lg px-3 py-2 text-[11px] uppercase tracking-[0.2em] opacity-75 transition hover:opacity-100"
                    href={`/${ia}`}
                    style={{ color: '#d4c49a' }}
                  >
                    {ia}
                  </a>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </nav>
  );
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [isTyping, setIsTyping] = useState(false);
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [availableIAs, setAvailableIAs] = useState<string[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [inputEnabled, setInputEnabled] = useState(false);
  const [inputPlaceholder, setInputPlaceholder] = useState('Speak your query to the World Tree...');

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    let cancelled = false;

    async function loadSession() {
      try {
        const sessionResponse = await fetch('/session-info');
        const sessionData = (await sessionResponse.json()) as SessionInfo;
        if (cancelled) {
          return;
        }

        setSession(sessionData);

        if (!sessionData.usuario) {
          setInputEnabled(false);
          setInputPlaceholder('Log in to consult Yggdrassil.');
          return;
        }

        setInputEnabled(true);
        setInputPlaceholder('Speak your query to the World Tree...');

        const storedMessages = parseStoredMessages(
          window.localStorage.getItem(storageKeyForUser(sessionData.usuario)),
        );
        if (storedMessages) {
          setMessages(storedMessages);
        }

        const usosResponse = await fetch('/usos');
        if (!usosResponse.ok || cancelled) {
          return;
        }

        const usos = (await usosResponse.json()) as Record<string, number>;
        const visibleIAs = ['hada', 'aries', 'fantasma', 'anima'].filter(ia => {
          const cantidad = usos[ia];
          return cantidad === -1 || typeof cantidad === 'number' && cantidad >= 0;
        });
        setAvailableIAs(visibleIAs);
      } catch {
        if (!cancelled) {
          setInputEnabled(false);
          setInputPlaceholder('Connection unavailable.');
        }
      }
    }

    loadSession();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!session?.usuario) {
      return;
    }

    window.localStorage.setItem(
      storageKeyForUser(session.usuario),
      JSON.stringify(serializeMessages(messages)),
    );
  }, [messages, session]);

  const statusLabel = useMemo(() => {
    if (!session?.usuario) {
      return 'Awaiting the seeker';
    }
    if (isTyping) {
      return 'The roots are listening';
    }
    return `Bound to ${session.usuario}`;
  }, [isTyping, session]);

  async function handleSend(content: string) {
    if (!session?.usuario || isTyping) {
      return;
    }

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const response = await fetch('/yggdrassil/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mensaje: content,
          id: session.usuario,
        }),
      });

      const payload = await response.json();
      const respuesta = typeof payload?.respuesta === 'string' && payload.respuesta.trim()
        ? payload.respuesta
        : 'The bark is silent. Try again in a moment.';

      setIsTyping(false);
      const assistantMsg: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: respuesta,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      setIsTyping(false);
      setMessages(prev => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: 'The roots cannot hear you right now. The connection to the grove is unstable.',
          timestamp: new Date(),
        },
      ]);
    }
  }

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
        <Navbar isAdmin={session?.rol === 'admin'} availableIAs={availableIAs} />

        {/* Header */}
        <header
          className="shrink-0 px-4 sm:px-8 pt-20 pb-4"
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
              {statusLabel}
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
          <ChatInput
            onSend={handleSend}
            disabled={!inputEnabled || isTyping}
            placeholder={inputPlaceholder}
          />
        </div>
      </div>
    </div>
  );
}
