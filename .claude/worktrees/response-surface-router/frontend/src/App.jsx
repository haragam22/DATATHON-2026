/**
 * App.jsx — KSP Crime Intelligence
 *
 * Routes:
 *   /            → Dashboard (Milestone 8: Hotspot map + trends + recommendations)
 *   /chat        → Chat interface (Milestones 1–4)
 *   /investigate → Investigation Board + Similar Cases + Entity Sidecar (Milestones 5–7)
 */

import { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Shield, Activity, MessageSquare, Network, ShieldCheck } from 'lucide-react';
import { healthCheck } from './services/api';
import { RoleProvider } from './context/RoleContext';
import RoleSelector from './components/common/RoleSelector';
import SecurityAuditModal from './components/common/SecurityAuditModal';
import SystemStatusModal from './components/common/SystemStatusModal';

// ---------------------------------------------------------------------------
// Page components
// ---------------------------------------------------------------------------

import DashboardPage from './components/dashboard/DashboardPage';
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
      <BrowserRouter>
        <div className="app-shell">
          {/* ── Top header bar ── */}
          <header className="app-header">
            <div className="app-header__brand">
              <Shield size={18} strokeWidth={1.5} color="var(--ksp-blue)" />
              <span className="app-header__name">KSP CRIME INTELLIGENCE</span>
              <span className="app-header__sub font-mono text-xs text-faint">
                Catalyst Datathon 2026 · PS1
              </span>
            </div>

            <nav className="app-header__nav">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `app-nav-link${isActive ? ' app-nav-link--active' : ''}`
                }
              >
                <Activity size={14} strokeWidth={1.5} />
                Dashboard
              </NavLink>
              <NavLink
                to="/chat"
                className={({ isActive }) =>
                  `app-nav-link${isActive ? ' app-nav-link--active' : ''}`
                }
              >
                <MessageSquare size={14} strokeWidth={1.5} />
                Chat
              </NavLink>
              <NavLink
                to="/investigate"
                className={({ isActive }) =>
                  `app-nav-link${isActive ? ' app-nav-link--active' : ''}`
                }
              >
                <Network size={14} strokeWidth={1.5} />
                Investigate
              </NavLink>
            </nav>

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

              {/* System Status Modal Trigger (Milestone 14) */}
              <div onClick={() => setIsSystemOpen(true)} className="cursor-pointer">
                <BackendStatusIndicator status={backendStatus} />
              </div>
            </div>
          </header>

          {/* ── Page content ── */}
          <main className="app-main">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/chat" element={<ChatWindow />} />
              <Route path="/investigate" element={<InvestigatePage />} />
            </Routes>
          </main>

          {/* Milestone 13 & 14 Modals */}
          <SecurityAuditModal isOpen={isSecurityOpen} onClose={() => setIsSecurityOpen(false)} />
          <SystemStatusModal isOpen={isSystemOpen} onClose={() => setIsSystemOpen(false)} />
        </div>
      </BrowserRouter>
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
