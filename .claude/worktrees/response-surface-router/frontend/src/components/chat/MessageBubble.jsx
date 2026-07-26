/**
 * MessageBubble — wraps a single user or assistant message.
 *
 * User messages: right-aligned, compact.
 * Assistant messages: full-width cards (ink-800 surface, line-700 border,
 * 4px radius) — "dashboards in miniature, not short text" (design.md).
 *
 * Assistant messages dispatch to EnvelopeDispatcher for rendering.
 */

import { useState } from 'react';
import { AlertCircle, Lock, LogIn } from 'lucide-react';
import EnvelopeDispatcher from './renderers/EnvelopeDispatcher';
import VerificationStamp from './VerificationStamp';
import ExplainabilityPanel from './ExplainabilityPanel';
import FollowUpButtons from './FollowUpButtons';
import './MessageBubble.css';

export default function MessageBubble({ message, onSelectCaseId }) {
  if (message.role === 'user') {
    return <UserBubble message={message} />;
  }
  return <AssistantBubble message={message} onSelectCaseId={onSelectCaseId} />;
}

// ── User message ──

function UserBubble({ message }) {
  return (
    <div className="msg msg--user">
      <div className="msg__content msg__content--user">
        <p>{message.content}</p>
      </div>
    </div>
  );
}

// ── Assistant message ──

function AssistantBubble({ message, onSelectCaseId }) {
  const [showExplainability, setShowExplainability] = useState(false);

  // Error state
  if (message.error) {
    return (
      <div className="msg msg--assistant msg--enter">
        <div className="msg__content msg__content--assistant msg__content--error">
          <ErrorDisplay
            error={message.error}
            status={message.errorStatus}
          />
        </div>
      </div>
    );
  }

  const envelope = message.envelope;
  const isAbstention = Boolean(envelope?.data?.clarifying_question);

  return (
    <div className="msg msg--assistant msg--enter">
      <div className="msg__wrapper">
        <div className="msg__content msg__content--assistant">
          {/* Verification Stamp (Top Right Header Element) */}
          {envelope && (
            <div className="msg__stamp-wrapper">
              <VerificationStamp
                confidenceScore={envelope.confidence_score}
                isAbstention={isAbstention}
                isExpanded={showExplainability}
                onToggleExpand={() => setShowExplainability((prev) => !prev)}
              />
            </div>
          )}

          {/* Envelope-dispatched main content */}
          <EnvelopeDispatcher envelope={envelope} />

          {/* Collapsible Explainability Panel */}
          {showExplainability && envelope && (
            <ExplainabilityPanel
              envelope={envelope}
              onSelectCaseId={onSelectCaseId}
            />
          )}
        </div>

        {/* Follow-up question chips */}
        {envelope?.follow_up_questions && (
          <FollowUpButtons questions={envelope.follow_up_questions} />
        )}
      </div>
    </div>
  );
}

// ── Error display ──

function ErrorDisplay({ error, status }) {
  // 401 → prompt login
  if (status === 401) {
    return (
      <div className="msg__error">
        <LogIn size={16} strokeWidth={1.5} className="text-amber" />
        <div>
          <span className="label-section text-amber">Authentication Required</span>
          <p className="text-sm text-muted">Please log in to continue.</p>
        </div>
      </div>
    );
  }

  // 403 → RBAC locked (design.md: dimmed + locked with tooltip)
  if (status === 403) {
    return (
      <div className="msg__error">
        <Lock size={16} strokeWidth={1.5} className="text-amber" />
        <div>
          <span className="label-section text-amber">Access Restricted</span>
          <p className="text-sm text-muted">{error}</p>
        </div>
      </div>
    );
  }

  // Other errors
  return (
    <div className="msg__error">
      <AlertCircle size={16} strokeWidth={1.5} className="text-red" />
      <div>
        <span className="label-section text-red">
          {status === 0 ? 'Connection Error' : `Error ${status || ''}`}
        </span>
        <p className="text-sm text-muted">{error}</p>
      </div>
    </div>
  );
}
