import { useState, useRef, KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <path d="M9 2L9 16M9 2L14 7M9 2L4 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export default function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [value, setValue] = useState('');
  const [focused, setFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  return (
    <div className="relative">
      {/* Decorative top border shimmer */}
      <div
        className="absolute -top-px left-1/4 right-1/4 h-px rounded-full opacity-50"
        style={{ background: 'linear-gradient(to right, transparent, rgba(180,143,64,0.5), transparent)' }}
      />

      <div
        className="flex items-end gap-3 p-4 transition-all duration-300"
        style={{
          background: 'linear-gradient(to top, rgba(5,10,6,0.98) 0%, rgba(8,18,10,0.92) 100%)',
          borderTop: '1px solid rgba(180,143,64,0.12)',
        }}
      >
        {/* Left rune decoration */}
        <div className="hidden sm:flex flex-col items-center gap-1 pb-3 opacity-30">
          <div className="w-px h-6" style={{ background: 'linear-gradient(to bottom, transparent, rgba(180,143,64,0.5))' }} />
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <polygon points="5,1 9,9 1,9" stroke="rgba(180,143,64,0.8)" strokeWidth="0.8" fill="none"/>
          </svg>
        </div>

        {/* Input wrapper */}
        <div className="flex-1 relative">
          <div
            className="relative rounded-2xl transition-all duration-300"
            style={{
              background: 'rgba(10, 22, 12, 0.9)',
              border: focused
                ? '1px solid rgba(180, 143, 64, 0.5)'
                : '1px solid rgba(180, 143, 64, 0.2)',
              boxShadow: focused
                ? '0 0 24px rgba(180,143,64,0.12), 0 0 60px rgba(180,143,64,0.04), inset 0 1px 0 rgba(180,143,64,0.08)'
                : '0 0 10px rgba(0,0,0,0.3)',
            }}
          >
            {/* Inner corner accents */}
            <span
              className="absolute top-2 left-3 text-[10px] transition-opacity duration-300"
              style={{ color: 'rgba(180,143,64,0.4)', opacity: focused ? 0.6 : 0.2 }}
            >
              ᚠ
            </span>
            <span
              className="absolute top-2 right-12 text-[10px] transition-opacity duration-300"
              style={{ color: 'rgba(180,143,64,0.4)', opacity: focused ? 0.6 : 0.2 }}
            >
              ᚱ
            </span>

            <textarea
              ref={textareaRef}
              value={value}
              onChange={e => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              onInput={handleInput}
              placeholder={placeholder ?? 'Habla tu consulta al Árbol del Mundo...'}
              rows={1}
              disabled={disabled}
              className="w-full resize-none bg-transparent outline-none px-5 py-3.5 pr-12 text-sm leading-relaxed placeholder-opacity-40"
              style={{
                fontFamily: 'Crimson Text, serif',
                fontSize: '1rem',
                color: '#e8dfc8',
                caretColor: '#c9a84c',
                minHeight: '52px',
              }}
            />

            {/* Send button */}
            <button
              onClick={handleSend}
              disabled={!value.trim() || disabled}
              className="absolute right-3 bottom-3 w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
              style={{
                background: value.trim() && !disabled
                  ? 'linear-gradient(135deg, rgba(180,143,64,0.3) 0%, rgba(140,100,40,0.3) 100%)'
                  : 'rgba(180,143,64,0.05)',
                border: '1px solid rgba(180,143,64,0.3)',
                color: '#c9a84c',
              }}
              onMouseEnter={e => {
                if (!(!value.trim() || disabled)) {
                  (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 0 16px rgba(180,143,64,0.3)';
                  (e.currentTarget as HTMLButtonElement).style.background = 'linear-gradient(135deg, rgba(180,143,64,0.4) 0%, rgba(140,100,40,0.4) 100%)';
                }
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLButtonElement).style.boxShadow = 'none';
                (e.currentTarget as HTMLButtonElement).style.background = value.trim() && !disabled
                  ? 'linear-gradient(135deg, rgba(180,143,64,0.3) 0%, rgba(140,100,40,0.3) 100%)'
                  : 'rgba(180,143,64,0.05)';
              }}
            >
              <SendIcon />
            </button>
          </div>
        </div>

        {/* Right rune decoration */}
        <div className="hidden sm:flex flex-col items-center gap-1 pb-3 opacity-30">
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <polygon points="5,1 9,9 1,9" stroke="rgba(180,143,64,0.8)" strokeWidth="0.8" fill="none"/>
          </svg>
          <div className="w-px h-6" style={{ background: 'linear-gradient(to bottom, rgba(180,143,64,0.5), transparent)' }} />
        </div>
      </div>

      {/* Hint text */}
      <div
        className="text-center pb-2 text-xs opacity-25"
        style={{ fontFamily: 'Inter, sans-serif', color: '#c9a84c' }}
      >
        Presiona Enter para enviar · Shift+Enter para nueva línea
      </div>
    </div>
  );
}
