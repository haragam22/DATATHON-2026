/**
 * ChatContext — conversation state for the chat interface.
 *
 * Manages: sessions list, active session, messages per session,
 * loading state, and backend session_id round-tripping.
 *
 * Uses useReducer + Context — no Redux needed at this scale.
 */

import { createContext, useContext, useReducer, useCallback } from 'react';
import { postQuery, ApiError } from '../services/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

let _idCounter = 0;
function uid() {
  return `msg-${Date.now()}-${++_idCounter}`;
}

function sessionUid() {
  return `sess-${Date.now()}-${++_idCounter}`;
}

function makeSession(title = 'New conversation') {
  return {
    localId: sessionUid(),
    backendSessionId: null,
    title,
    createdAt: Date.now(),
    messages: [],
  };
}

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

const firstSession = makeSession();

const initialState = {
  sessions: [firstSession],
  activeSessionLocalId: firstSession.localId,
  isLoading: false,
};

// ---------------------------------------------------------------------------
// Reducer
// ---------------------------------------------------------------------------

function chatReducer(state, action) {
  switch (action.type) {
    case 'CREATE_SESSION': {
      const s = makeSession();
      return {
        ...state,
        sessions: [s, ...state.sessions],
        activeSessionLocalId: s.localId,
      };
    }

    case 'SET_ACTIVE_SESSION':
      return { ...state, activeSessionLocalId: action.localId };

    case 'SET_LOADING':
      return { ...state, isLoading: action.value };

    case 'ADD_USER_MESSAGE': {
      return {
        ...state,
        sessions: state.sessions.map((s) =>
          s.localId === state.activeSessionLocalId
            ? {
                ...s,
                messages: [
                  ...s.messages,
                  {
                    id: uid(),
                    role: 'user',
                    content: action.text,
                    envelope: null,
                    error: null,
                    errorStatus: null,
                    timestamp: Date.now(),
                  },
                ],
                // Use first few words of the very first message as the title
                title:
                  s.messages.length === 0
                    ? action.text.slice(0, 60) + (action.text.length > 60 ? '…' : '')
                    : s.title,
              }
            : s
        ),
      };
    }

    case 'ADD_ASSISTANT_RESPONSE': {
      return {
        ...state,
        sessions: state.sessions.map((s) =>
          s.localId === state.activeSessionLocalId
            ? {
                ...s,
                backendSessionId:
                  action.envelope?.data?.session_id ?? s.backendSessionId,
                messages: [
                  ...s.messages,
                  {
                    id: uid(),
                    role: 'assistant',
                    content: extractAnswerText(action.envelope),
                    envelope: action.envelope,
                    error: null,
                    errorStatus: null,
                    timestamp: Date.now(),
                  },
                ],
              }
            : s
        ),
      };
    }

    case 'ADD_ERROR_MESSAGE': {
      return {
        ...state,
        sessions: state.sessions.map((s) =>
          s.localId === state.activeSessionLocalId
            ? {
                ...s,
                messages: [
                  ...s.messages,
                  {
                    id: uid(),
                    role: 'assistant',
                    content: null,
                    envelope: null,
                    error: action.error,
                    errorStatus: action.status ?? null,
                    timestamp: Date.now(),
                  },
                ],
              }
            : s
        ),
      };
    }

    case 'DELETE_SESSION': {
      const remaining = state.sessions.filter(
        (s) => s.localId !== action.localId
      );
      if (remaining.length === 0) {
        const fresh = makeSession();
        return {
          ...state,
          sessions: [fresh],
          activeSessionLocalId: fresh.localId,
        };
      }
      return {
        ...state,
        sessions: remaining,
        activeSessionLocalId:
          state.activeSessionLocalId === action.localId
            ? remaining[0].localId
            : state.activeSessionLocalId,
      };
    }

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Extract answer text from envelope for display / accessibility
// ---------------------------------------------------------------------------

function extractAnswerText(envelope) {
  if (!envelope) return '';

  // Pipeline error (200 with data.error)
  if (envelope.data?.error) return envelope.data.error;

  // Try common fields the backend might use for the answer text
  const d = envelope.data;
  if (typeof d === 'string') return d;
  if (d?.clarifying_question) return d.clarifying_question;
  if (d?.answer) return d.answer;
  if (d?.answer_text) return d.answer_text;
  if (d?.text) return d.text;
  if (d?.message) return d.message;
  if (d?.summary) return d.summary;

  // For card/chart/map types, there might not be a text answer
  return '';
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  // Get the active session object
  const activeSession =
    state.sessions.find((s) => s.localId === state.activeSessionLocalId) ??
    state.sessions[0];

  // ------ Actions ------

  const createSession = useCallback(() => {
    dispatch({ type: 'CREATE_SESSION' });
  }, []);

  const setActiveSession = useCallback((localId) => {
    dispatch({ type: 'SET_ACTIVE_SESSION', localId });
  }, []);

  const deleteSession = useCallback((localId) => {
    dispatch({ type: 'DELETE_SESSION', localId });
  }, []);

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || state.isLoading) return;

      dispatch({ type: 'ADD_USER_MESSAGE', text: text.trim() });
      dispatch({ type: 'SET_LOADING', value: true });

      try {
        const envelope = await postQuery(text.trim(), activeSession.backendSessionId);

        // POST /api/query returns 200 even on pipeline failure —
        // check data.error in the body.
        if (envelope?.data?.error) {
          dispatch({
            type: 'ADD_ASSISTANT_RESPONSE',
            envelope: { ...envelope, response_type: 'text' },
          });
        } else {
          dispatch({ type: 'ADD_ASSISTANT_RESPONSE', envelope });
        }
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : 'An unexpected error occurred';
        const status = err instanceof ApiError ? err.status : 500;

        dispatch({ type: 'ADD_ERROR_MESSAGE', error: message, status });
      } finally {
        dispatch({ type: 'SET_LOADING', value: false });
      }
    },
    [state.isLoading, activeSession]
  );

  const value = {
    sessions: state.sessions,
    activeSession,
    isLoading: state.isLoading,
    createSession,
    setActiveSession,
    deleteSession,
    sendMessage,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used within <ChatProvider>');
  return ctx;
}
