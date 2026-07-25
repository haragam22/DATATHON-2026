/**
 * RoleContext — Milestone 9: Role-Based Access Control (RBAC).
 *
 * Managed Roles:
 *   - Investigator: Baseline query, network, maps, charts, evidence, export
 *   - Analyst: Same as Investigator
 *   - Supervisor: + Entity context, risk scoring, financial trail
 *   - Policymaker: + Policy insights / admin scopes
 */

import { createContext, useContext, useState, useCallback } from 'react';

const ROLE_SCOPES = {
  Investigator: [
    'query',
    'network',
    'similar-cases',
    'aggregates',
    'hotspots',
    'evidence',
    'conversation-export',
  ],
  Analyst: [
    'query',
    'network',
    'similar-cases',
    'aggregates',
    'hotspots',
    'evidence',
    'conversation-export',
  ],
  Supervisor: [
    'query',
    'network',
    'similar-cases',
    'aggregates',
    'hotspots',
    'evidence',
    'conversation-export',
    'entity-context',
    'risk-score',
    'financial-trail',
  ],
  Policymaker: [
    'query',
    'network',
    'similar-cases',
    'aggregates',
    'hotspots',
    'evidence',
    'conversation-export',
    'entity-context',
    'risk-score',
    'financial-trail',
    'admin-backfill-evidence',
  ],
};

const RoleContext = createContext(null);

export function RoleProvider({ children }) {
  // Default role for dev mode: Supervisor (full access for testing)
  const [role, setRoleState] = useState(() => {
    return localStorage.getItem('ksp_user_role') || 'Supervisor';
  });

  const setRole = useCallback((newRole) => {
    if (ROLE_SCOPES[newRole]) {
      setRoleState(newRole);
      localStorage.setItem('ksp_user_role', newRole);
    }
  }, []);

  const hasScope = useCallback((scope) => {
    const scopes = ROLE_SCOPES[role] || [];
    return scopes.includes(scope);
  }, [role]);

  return (
    <RoleContext.Provider
      value={{
        role,
        setRole,
        hasScope,
        allRoles: Object.keys(ROLE_SCOPES),
      }}
    >
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error('useRole must be used within a RoleProvider');
  }
  return context;
}
