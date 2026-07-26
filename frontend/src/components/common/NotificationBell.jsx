/**
 * NotificationBell — header icon + dropdown history of SOS/112 alerts.
 * Toasts (SosNotificationBar) still auto-vanish after 2s; every alert also
 * lands here so nothing is lost once its toast disappears.
 */

import { useState, useRef, useEffect } from 'react';
import { Bell, Siren, MapPin, User, Phone } from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';
import './NotificationBell.css';

export default function NotificationBell() {
  const { history, unreadCount, markAllRead, clearHistory } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);
  const panelRef = useRef(null);

  const toggle = () => {
    setIsOpen((prev) => {
      if (!prev) markAllRead();
      return !prev;
    });
  };

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const onClick = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) setIsOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [isOpen]);

  return (
    <div className="notification-bell" ref={panelRef}>
      <button
        className="btn-icon notification-bell__trigger"
        onClick={toggle}
        aria-label="Notifications"
        aria-expanded={isOpen}
        type="button"
      >
        <Bell size={18} strokeWidth={1.5} />
        {unreadCount > 0 && (
          <span className="notification-bell__badge font-mono">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="notification-bell__panel surface-float animate-fade-in">
          <div className="notification-bell__panel-header">
            <span className="label-section">Notifications</span>
            {history.length > 0 && (
              <button className="notification-bell__clear font-mono text-xs" onClick={clearHistory}>
                Clear all
              </button>
            )}
          </div>

          {history.length === 0 ? (
            <div className="notification-bell__empty text-faint text-xs">
              No notifications yet.
            </div>
          ) : (
            <ul className="notification-bell__list">
              {history.map((t) => (
                <li key={t._key} className="notification-bell__item">
                  <Siren size={14} className="text-red notification-bell__item-icon" />
                  <div className="notification-bell__item-body">
                    <span className="notification-bell__item-type">{t.emergency_type}</span>
                    <span className="notification-bell__item-meta font-mono text-xs text-faint">
                      <User size={10} /> {t.caller_name}
                      <Phone size={10} /> {t.caller_phone}
                      <MapPin size={10} /> {t.lat.toFixed(3)}, {t.lon.toFixed(3)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
