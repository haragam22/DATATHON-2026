/**
 * RoleSelector — Milestone 9: Header Role Selector Widget.
 *
 * Displays active user role badge with role-specific color code per design.md:
 *   - Investigator: ink-700 (neutral)
 *   - Analyst: ksp-blue
 *   - Supervisor: ksp-gold
 *   - Policymaker: signal-green
 */

import { useRole } from '../../context/RoleContext';
import { UserCheck } from 'lucide-react';
import './RoleSelector.css';

const ROLE_COLORS = {
  Investigator: 'var(--text-400)',
  Analyst:      'var(--stamp-ink)',
  Supervisor:   'var(--ksp-gold)',
  Policymaker:  'var(--signal-green)',
};

export default function RoleSelector() {
  const { role, setRole, allRoles } = useRole();

  const activeColor = ROLE_COLORS[role] || 'var(--ink-700)';

  return (
    <div className="role-selector font-mono text-xs">
      <span
        className="role-selector__dot"
        style={{ background: activeColor, borderColor: activeColor }}
        aria-hidden="true"
      />
      <UserCheck size={12} className="text-muted" />
      <select
        value={role}
        onChange={(e) => setRole(e.target.value)}
        className="role-selector__select font-mono"
        title="Switch user role for RBAC testing"
      >
        {allRoles.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
    </div>
  );
}
