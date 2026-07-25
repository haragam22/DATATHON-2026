/**
 * ResponseEvidence — renders evidence response_type (from /api/evidence/<case_id>).
 *
 * design.md: every evidence tile carries a persistent watermark —
 * "SYNTHETIC / PLACEHOLDER" in text-600 at low opacity across the tile corner.
 */

import { useState } from 'react';
import { FileVideo, FileAudio, FileImage, FileText, Eye } from 'lucide-react';
import EvidenceModal from '../EvidenceModal';
import './ResponseRenderers.css';

const TYPE_ICONS = {
  video: FileVideo,
  audio: FileAudio,
  image: FileImage,
  document: FileText,
};

export default function ResponseEvidence({ envelope }) {
  const [selectedItem, setSelectedItem] = useState(null);
  const { data } = envelope;
  const items = data?.items || data?.evidence || [];

  if (!Array.isArray(items) || items.length === 0) {
    return (
      <div className="response-evidence">
        <p className="text-muted text-sm">No evidence items found for this case.</p>
      </div>
    );
  }

  return (
    <div className="response-evidence">
      <div className="response-evidence__header label-section">
        Evidence — {items.length} item{items.length !== 1 ? 's' : ''}
      </div>
      <div className="response-evidence__grid">
        {items.map((item, i) => (
          <EvidenceTile
            key={item.evidence_id ?? item.EvidenceID ?? i}
            item={item}
            onSelect={() => setSelectedItem(item)}
          />
        ))}
      </div>

      {selectedItem && (
        <EvidenceModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}
    </div>
  );
}

function EvidenceTile({ item, onSelect }) {
  const type = (item.evidence_type ?? item.EvidenceType ?? 'document').toLowerCase();
  const Icon = TYPE_ICONS[type] || FileText;
  const description =
    item.description ?? item.Description ?? item.file_name ?? 'Evidence item';

  return (
    <div
      className="evidence-tile surface-raised"
      onClick={onSelect}
      title="Click to open interactive media viewer"
    >
      {/* Persistent watermark — design.md constraint made visible */}
      <div className="evidence-tile__watermark" aria-hidden="true">
        SYNTHETIC / PLACEHOLDER
      </div>

      <div className="evidence-tile__icon">
        <Icon size={24} strokeWidth={1.5} />
      </div>
      <div className="evidence-tile__info">
        <div className="flex items-center justify-between">
          <span className="evidence-tile__type chip chip-muted">{type}</span>
          <Eye size={12} className="text-faint" />
        </div>
        <p className="evidence-tile__desc text-sm">{description}</p>
        {item.uploaded_date && (
          <span className="evidence-tile__date text-xs text-faint font-mono">
            {item.uploaded_date}
          </span>
        )}
      </div>
    </div>
  );
}
