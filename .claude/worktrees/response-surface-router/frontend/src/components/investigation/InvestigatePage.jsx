/**
 * InvestigatePage — Container page for Milestones 5, 6, 7.
 *
 * Layout:
 * ┌── Similar Cases ──┬──── Investigation Board (graph) ────┬── Entity Sidecar ──┐
 * │  (left rail)       │  (center, flex-1)                   │  (right, if open)  │
 * └───────────────────┴─────────────────────────────────────┴────────────────────┘
 *
 * Interactions:
 * - SimilarCasesPanel.onSelectCase → loads that case_id in the Investigation Board
 * - InvestigationBoard.onSelectEntity → opens EntitySidecar for that accused_id
 * - EntitySidecar.onSelectCase → navigates back to the board for that case_id
 */

import { useState, useCallback } from 'react';
import InvestigationBoard from './InvestigationBoard';
import SimilarCasesPanel from './SimilarCasesPanel';
import EntitySidecar from './EntitySidecar';
import './InvestigatePage.css';

export default function InvestigatePage() {
  const [activeCaseId, setActiveCaseId] = useState(1);
  const [selectedEntity, setSelectedEntity] = useState(null); // { id, name }

  const handleSelectCase = useCallback((caseId) => {
    setActiveCaseId(caseId);
    setSelectedEntity(null); // Close sidecar when switching cases
  }, []);

  const handleSelectEntity = useCallback((node) => {
    // node: { id, name, isSeed }
    setSelectedEntity({ id: node.id, name: node.name });
  }, []);

  const handleCloseSidecar = useCallback(() => {
    setSelectedEntity(null);
  }, []);

  return (
    <div className="investigate-page">
      {/* Left Rail: Similar Cases */}
      <div className="investigate-page__sidebar">
        <SimilarCasesPanel
          caseId={activeCaseId}
          onSelectCase={handleSelectCase}
        />
      </div>

      {/* Center: Investigation Board */}
      <div className="investigate-page__main">
        <InvestigationBoard
          key={activeCaseId}
          initialCaseId={activeCaseId}
          onSelectEntity={handleSelectEntity}
        />
      </div>

      {/* Right: Entity Sidecar (conditional) */}
      {selectedEntity && (
        <div className="investigate-page__sidecar">
          <EntitySidecar
            key={selectedEntity.id}
            accusedId={selectedEntity.id}
            accusedName={selectedEntity.name}
            onClose={handleCloseSidecar}
            onSelectCase={handleSelectCase}
          />
        </div>
      )}
    </div>
  );
}
