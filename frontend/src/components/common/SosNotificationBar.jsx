/**
 * SosNotificationBar — transient toast display for fresh SOS/112 alerts.
 * Mounted once at app-shell level in App.jsx (global, not per-page).
 *
 * Alert state (polling, history, unread count) lives in NotificationContext;
 * this component only renders the currently-live toasts, which auto-expire
 * themselves (see TOAST_LIFETIME_MS in the context) — dismiss here just
 * clears one early.
 */

import { Siren, X, MapPin, User, Phone } from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';
import './SosNotificationBar.css';

export default function SosNotificationBar() {
  const { toasts, dismissToast } = useNotifications();

  if (toasts.length === 0) return null;

  return (
    <div className="sos-bar" role="alert" aria-live="assertive">
      {toasts.map((t) => (
        <div key={t._key} className="sos-bar__toast">
          <Siren size={16} className="text-red sos-bar__icon" />
          <div className="sos-bar__content">
            <span className="sos-bar__type">{t.emergency_type}</span>
            <span className="sos-bar__meta">
              <User size={11} /> {t.caller_name}
              <Phone size={11} /> {t.caller_phone}
              <MapPin size={11} /> {t.lat.toFixed(3)}, {t.lon.toFixed(3)}
            </span>
          </div>
          <button
            className="sos-bar__dismiss btn-icon"
            onClick={() => dismissToast(t._key)}
            aria-label="Dismiss alert"
            type="button"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
