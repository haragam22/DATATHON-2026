/**
 * Sidebar — session list + new session button.
 * Shows all local sessions, highlights the active one.
 * Role badge placeholder (filled in at RBAC milestone).
 */

import { Plus, MessageSquare, Trash2 } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import './Sidebar.css';

export default function Sidebar() {
  const { sessions, activeSession, createSession, setActiveSession, deleteSession } =
    useChat();

  return (
    <aside className="sidebar">
      {/* Header */}
      <div className="sidebar__header">
        <button
          className="sidebar__new-btn btn btn-ghost"
          onClick={createSession}
        >
          <Plus size={14} strokeWidth={1.5} />
          New session
        </button>
      </div>

      {/* Sessions list */}
      <nav className="sidebar__sessions">
        {sessions.map((s) => {
          const isActive = s.localId === activeSession.localId;
          return (
            <div
              key={s.localId}
              className={`sidebar__session${isActive ? ' sidebar__session--active' : ''}`}
              onClick={() => setActiveSession(s.localId)}
              title={s.title}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setActiveSession(s.localId); }}
            >
              <span className="sidebar__session-dot" aria-hidden="true" />
              <MessageSquare size={13} strokeWidth={1.5} />
              <span className="sidebar__session-title">{s.title}</span>
              <button
                className="sidebar__session-delete btn-icon"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSession(s.localId);
                }}
                title="Delete session"
                aria-label="Delete session"
              >
                <Trash2 size={12} strokeWidth={1.5} />
              </button>
            </div>
          );
        })}
      </nav>

      {/* Role badge placeholder — RBAC milestone */}
      <div className="sidebar__footer">
        <span className="sidebar__role-badge chip chip-muted">
          <span className="sidebar__role-dot" aria-hidden="true" />
          Role: —
        </span>
      </div>
    </aside>
  );
}
