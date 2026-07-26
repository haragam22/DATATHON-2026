/**
 * NotificationContext — shared SOS/112 alert state.
 *
 * Polls GET /api/sos-alerts once here (was duplicated toast-only logic in
 * SosNotificationBar). Keeps two views over the same alert stream:
 *   - toasts: transient, auto-expire after TOAST_LIFETIME_MS
 *   - history: everything ever seen this session, capped at MAX_HISTORY,
 *     surfaced via the header notification bell (read/unread tracked here
 *     so the bell badge and the toast popups never drift out of sync).
 */

import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { getSosAlerts, ApiError } from '../services/api';

const POLL_INTERVAL_MS = 20_000;
const TOAST_LIFETIME_MS = 2_000;
const MAX_HISTORY = 50;

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const [history, setHistory] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const seenKeys = useRef(new Set());
  const toastTimers = useRef(new Map());

  useEffect(() => {
    let cancelled = false;

    const poll = () => {
      getSosAlerts()
        .then((envelope) => {
          if (cancelled) return;
          const alerts = envelope?.data?.alerts || [];
          const fresh = alerts
            .map((a) => ({ ...a, _key: `${a.caller_phone}-${a.received_at}`, _seenAt: Date.now() }))
            .filter((a) => !seenKeys.current.has(a._key));
          if (fresh.length === 0) return;
          fresh.forEach((a) => seenKeys.current.add(a._key));

          setToasts((prev) => [...fresh, ...prev]);
          setHistory((prev) => [...fresh, ...prev].slice(0, MAX_HISTORY));
          setUnreadCount((prev) => prev + fresh.length);

          fresh.forEach((a) => {
            const timer = setTimeout(() => {
              setToasts((prev) => prev.filter((t) => t._key !== a._key));
              toastTimers.current.delete(a._key);
            }, TOAST_LIFETIME_MS);
            toastTimers.current.set(a._key, timer);
          });
        })
        .catch((err) => {
          // ApiError swallowed at the UI layer — a failed poll shouldn't
          // spam the bar with error toasts, just skip this tick.
          if (!(err instanceof ApiError)) throw err;
        });
    };

    poll();
    const intervalId = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
      toastTimers.current.forEach(clearTimeout);
    };
  }, []);

  const dismissToast = useCallback((key) => {
    const timer = toastTimers.current.get(key);
    if (timer) {
      clearTimeout(timer);
      toastTimers.current.delete(key);
    }
    setToasts((prev) => prev.filter((t) => t._key !== key));
  }, []);

  const markAllRead = useCallback(() => setUnreadCount(0), []);

  const clearHistory = useCallback(() => {
    setHistory([]);
    setUnreadCount(0);
  }, []);

  return (
    <NotificationContext.Provider
      value={{ toasts, history, unreadCount, dismissToast, markAllRead, clearHistory }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}
