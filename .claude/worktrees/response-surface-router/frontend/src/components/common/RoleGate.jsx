/**
 * RoleGate — Milestone 9: RBAC Gating Component.
 *
 * Implements design.md's rule:
 * Gated features are NOT hidden entirely — they render dimmed/disabled with a
 * lock icon and tooltip ("Requires Supervisor access") to explicitly communicate
 * boundary governance to the user.
 *
 * Props:
 *   - scope: string (e.g. 'entity-context', 'risk-score', 'financial-trail')
 *   - requiredRoleLabel?: string (e.g. 'Supervisor')
 *   - children: ReactNode
 */

import { useRole } from '../../context/RoleContext';
import { Lock } from 'lucide-react';
import './RoleGate.css';

export default function RoleGate({ scope, requiredRoleLabel = 'Supervisor', children }) {
  const { hasScope } = useRole();
  const isAllowed = hasScope(scope);

  if (isAllowed) {
    return <>{children}</>;
  }

  return (
    <div
      className="role-gate role-gate--locked"
      title={`Requires ${requiredRoleLabel} role access`}
    >
      <div className="role-gate__lock-overlay">
        <div className="role-gate__badge font-mono text-xs">
          <Lock size={12} className="text-amber" />
          <span>Requires {requiredRoleLabel} Access</span>
        </div>
      </div>
      <div className="role-gate__content" aria-disabled="true">
        {children}
      </div>
    </div>
  );
}
