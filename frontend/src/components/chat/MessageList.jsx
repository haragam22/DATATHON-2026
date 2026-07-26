/**
 * MessageList — scrollable message area with auto-scroll-to-bottom.
 * Shows a typing indicator when the backend is processing.
 */

import { useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';
import { useRole } from '../../context/RoleContext';
import MessageBubble from './MessageBubble';
import NetworkDots from './NetworkDots';
import logo from '../../assets/logo.png';
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
  const { role } = useRole();

  // Ordered so the two visual-shaped answers (map, category breakdown) lead —
  // these reliably render a map/bar-list card, not just prose. Sourced from
  // docs/sample_questions.md, verified live against the backend.
  const starterPrompts = [
    'Map crime hotspots across Karnataka',
    'Show top 5 crime categories in Bengaluru City',
    'How many murder cases were registered in 2024?',
    'List repeat offenders with >2 prior cases',
  ];

  const hour = new Date().getHours();
  const timeGreeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="message-list__empty">
      <NetworkDots />

      <div className="message-list__empty-content">
        <img src={logo} alt="" className="message-list__logo" aria-hidden="true" />

        <h1 className="message-list__greeting">
          {timeGreeting}{role ? `, ${role}` : ''}
        </h1>
        <p className="text-muted text-sm">
          Ask a question about KSP case records, network relationships, or crime hotspots.
        </p>

        <div className="message-list__starters">
          {starterPrompts.map((prompt, idx) => (
            <button
              key={idx}
              className="message-list__starter-btn font-mono text-xs"
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
