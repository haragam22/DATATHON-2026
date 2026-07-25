/**
 * FollowUpButtons — Renders suggested follow-up questions from backend.
 *
 * Placed beneath assistant response cards.
 * Clicking a chip sends that question directly into the active chat session.
 */

import { CornerDownRight } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import './FollowUpButtons.css';

export default function FollowUpButtons({ questions }) {
  const { sendMessage, isLoading } = useChat();

  if (!Array.isArray(questions) || questions.length === 0) {
    return null;
  }

  return (
    <div className="follow-up-buttons">
      <span className="follow-up-buttons__label text-xs text-faint font-mono">
        SUGGESTED FOLLOW-UPS:
      </span>
      <div className="follow-up-buttons__list">
        {questions.map((q, idx) => (
          <button
            key={idx}
            className="follow-up-chip"
            onClick={() => sendMessage(q)}
            disabled={isLoading}
            title={`Ask: "${q}"`}
          >
            <CornerDownRight size={12} className="follow-up-chip__icon" />
            <span className="follow-up-chip__text">{q}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
