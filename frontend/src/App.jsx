/**
 * App.jsx — KSP Crime Intelligence
 *
 * Chat-first shell: chat is the single entry point at "/". Investigate and
 * Patrol stay wired as routes but are deep-link only (reached from a case
 * citation or an in-answer action, never from top nav) — see
 * docs/superpowers/specs (chat-first restructuring plan). DashboardPage is
 * intentionally unrouted: its content now surfaces as chat envelope cards
 * (hotspot map, trend charts, PCR feed) instead of a standalone page.
 */

import { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Shield, ShieldCheck } from 'lucide-react';
import { healthCheck } from './services/api';
import { RoleProvider } from './context/RoleContext';
import { NotificationProvider } from './context/NotificationContext';
import RoleSelector from './components/common/RoleSelector';
import SecurityAuditModal from './components/common/SecurityAuditModal';
import SystemStatusModal from './components/common/SystemStatusModal';
import SosNotificationBar from './components/common/SosNotificationBar';
import NotificationBell from './components/common/NotificationBell';
import ThemeToggle from './components/common/ThemeToggle';

// ---------------------------------------------------------------------------
// Page components
// ---------------------------------------------------------------------------

import PatrolPage from './components/dashboard/PatrolPage';
import ChatWindow from './components/chat/ChatWindow';
import InvestigatePage from './components/investigation/InvestigatePage';

// ---------------------------------------------------------------------------
// App shell
// ---------------------------------------------------------------------------

export default function App() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [isSecurityOpen, setIsSecurityOpen] = useState(false);
  const [isSystemOpen, setIsSystemOpen] = useState(false);

  useEffect(() => {
    healthCheck()
      .then((res) => {
        if (res?.status === 'success') setBackendStatus('ok');
        else setBackendStatus('unexpected');
      })
      .catch(() => setBackendStatus('error'));
  }, []);

  return (
    <RoleProvider>
      <NotificationProvider>
      <BrowserRouter>
        <div className="app-shell">
          {/* ── Top header bar ── */}
          <header className="app-header">
            <div className="app-header__brand">
              <Shield size={18} strokeWidth={1.5} color="var(--ksp-gold)" />
              <span className="app-header__name">KSP CRIME INTELLIGENCE</span>
              <span className="app-header__sub font-mono text-xs text-faint">
                Catalyst Datathon 2026 · PS1
              </span>
            </div>

            <div className="app-header__status flex items-center gap-3">
              {/* Security Audit Modal Trigger (Milestone 13) */}
              <button
                className="btn-icon text-gold hover:text-white"
                onClick={() => setIsSecurityOpen(true)}
                title="Security Guardrails & Red-Team Audit"
              >
                <ShieldCheck size={18} />
              </button>

              <RoleSelector />

              <ThemeToggle />

              <NotificationBell />

              {/* System Status Modal Trigger (Milestone 14) */}
              <div onClick={() => setIsSystemOpen(true)} className="cursor-pointer">
                <BackendStatusIndicator status={backendStatus} />
              </div>
            </div>
          </header>

          {/* ── Page content ── */}
          <main className="app-main">
            <Routes>
              <Route path="/" element={<ChatWindow />} />
              <Route path="/investigate" element={<InvestigatePage />} />
              <Route path="/patrol" element={<PatrolPage />} />
            </Routes>
          </main>

          {/* Milestone 13 & 14 Modals */}
          <SecurityAuditModal isOpen={isSecurityOpen} onClose={() => setIsSecurityOpen(false)} />
          <SystemStatusModal isOpen={isSystemOpen} onClose={() => setIsSystemOpen(false)} />

          {/* Feature 4: global SOS/112 notification bar */}
          <SosNotificationBar />
        </div>
      </BrowserRouter>
      </NotificationProvider>
    </RoleProvider>
  );
}

// ---------------------------------------------------------------------------
// BackendStatusIndicator
// ---------------------------------------------------------------------------

function BackendStatusIndicator({ status }) {
  const map = {
    checking:   { dot: 'var(--signal-amber)', label: 'Connecting…' },
    ok:         { dot: 'var(--signal-green)', label: 'Backend live' },
    unexpected: { dot: 'var(--signal-amber)', label: 'Unexpected response' },
    error:      { dot: 'var(--signal-red)',   label: 'Backend unreachable' },
  };
  const { dot, label } = map[status] ?? map.checking;

  return (
    <span className="backend-status font-mono text-xs text-faint">
      <span
        className="backend-status__dot"
        style={{ background: dot }}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}
