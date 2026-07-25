/**
 * MessageList — scrollable message area with auto-scroll-to-bottom.
 * Shows a typing indicator when the backend is processing.
 */

import { useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';
import MessageBubble from './MessageBubble';
import './MessageList.css';

export default function MessageList() {
  const { activeSession, isLoading } = useChat();
  const bottomRef = useRef(null);
  const containerRef = useRef(null);

  const messages = activeSession?.messages ?? [];

  // Auto-scroll to bottom on new messages or loading state change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, isLoading]);

  return (
    <div className="message-list" ref={containerRef}>
      {messages.length === 0 && !isLoading && <EmptyState />}

      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isLoading && <TypingIndicator />}

      <div ref={bottomRef} className="message-list__anchor" />
    </div>
  );
}

// ── Empty state ──

function EmptyState() {
  const { sendMessage } = useChat();

  const starterPrompts = [
    'Show top 5 crime categories in Bengaluru City',
    'How many murder cases were registered in 2024?',
    'List repeat offenders with >2 prior cases',
    'Map crime hotspots across Karnataka',
  ];

  return (
    <div className="message-list__empty">
      <div className="message-list__empty-icon" aria-hidden="true">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="24" r="23" stroke="var(--line-700)" strokeWidth="1" />
          <circle cx="24" cy="24" r="16" stroke="var(--line-700)" strokeWidth="1" strokeDasharray="4 3" />
          <text
            x="24"
            y="26"
            textAnchor="middle"
            fill="var(--text-600)"
            fontFamily="var(--font-mono)"
            fontSize="11"
          >
            KSP
          </text>
        </svg>
      </div>
      <p className="text-muted text-sm font-medium">
        KSP Crime Intelligence Assistant
      </p>
      <p className="text-faint text-xs">
        Ask natural language questions to query live crime records, network graphs, and hotspot overlays.
      </p>

      <div className="message-list__starters">
        <span className="label-section text-xs block margin-top-1">Suggested Queries</span>
        <div className="message-list__starter-grid">
          {starterPrompts.map((prompt, idx) => (
            <button
              key={idx}
              className="chip chip-blue message-list__starter-btn font-mono text-xs"
              onClick={() => sendMessage(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Typing indicator ──

function TypingIndicator() {
  return (
    <div className="msg msg--assistant msg--enter">
      <div className="msg__content msg__content--assistant typing-indicator">
        <span className="typing-indicator__dot" />
        <span className="typing-indicator__dot" />
        <span className="typing-indicator__dot" />
      </div>
    </div>
  );
}
