/**
 * EvidenceModal — Milestone 10: Interactive Evidence Media Player & Viewer.
 *
 * Requirements (design.md / frontend.md):
 *   - Modal dialog for inspecting video, audio, image, and document evidence
 *   - Persistent diagonal "SYNTHETIC / PLACEHOLDER" watermark across preview viewport
 *   - Shows full metadata (Evidence ID, Case ID, File Type, Uploaded Date, Description)
 */

import { X, FileVideo, FileAudio, FileImage, FileText, Download } from 'lucide-react';
import './EvidenceModal.css';

const TYPE_ICONS = {
  video: FileVideo,
  audio: FileAudio,
  image: FileImage,
  document: FileText,
};

export default function EvidenceModal({ item, onClose }) {
  if (!item) return null;

  const type = (item.evidence_type ?? item.EvidenceType ?? 'document').toLowerCase();
  const Icon = TYPE_ICONS[type] || FileText;
  const description =
    item.description ?? item.Description ?? item.file_name ?? 'Evidence record';
  const evidenceId = item.evidence_id ?? item.EvidenceID ?? '—';
  const caseId = item.case_id ?? item.CaseID_FK ?? '—';
  const date = item.uploaded_date ?? item.Timestamp ?? '—';

  return (
    <div className="evidence-modal-backdrop animate-fade-in" onClick={onClose}>
      <div
        className="evidence-modal surface-float animate-slide-in"
        onClick={(e) => e.stopPropagation()} // Prevent click-outside closing
      >
        {/* ── Modal Header ── */}
        <div className="evidence-modal__header">
          <div className="flex items-center gap-2">
            <Icon size={18} className="text-gold" />
            <span className="font-mono text-sm font-semibold text-100 uppercase">
              Evidence File #{evidenceId}
            </span>
            <span className="chip chip-gold font-mono text-xs">Case #{caseId}</span>
          </div>
          <button
            className="btn-icon evidence-modal__close"
            onClick={onClose}
            title="Close viewer"
          >
            <X size={18} />
          </button>
        </div>

        {/* ── Media Viewport (with persistent watermark) ── */}
        <div className="evidence-modal__viewport surface-base">
          {/* SYNTHETIC / PLACEHOLDER Watermark — strict design constraint */}
          <div className="evidence-modal__watermark-banner font-mono text-xs" aria-hidden="true">
            ✦ SYNTHETIC / PLACEHOLDER DEMO EVIDENCE ✦
          </div>

          <div className="evidence-modal__media-container">
            {type === 'image' && (
              <img
                src={item.file_url || 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800&auto=format&fit=crop'}
                alt={description}
                className="evidence-modal__img"
              />
            )}

            {type === 'video' && (
              <div className="evidence-modal__video-wrapper">
                <video
                  controls
                  autoPlay={false}
                  poster="https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800&auto=format&fit=crop"
                  className="evidence-modal__video"
                >
                  <source
                    src={item.file_url || 'https://www.w3schools.com/html/mov_bbb.mp4'}
                    type="video/mp4"
                  />
                  Your browser does not support HTML5 video playback.
                </video>
              </div>
            )}

            {type === 'audio' && (
              <div className="evidence-modal__audio-wrapper">
                <FileAudio size={48} className="text-gold margin-top-1" />
                <span className="font-mono text-xs text-muted">Audio Recording File</span>
                <audio controls className="evidence-modal__audio">
                  <source
                    src={item.file_url || 'https://www.w3schools.com/html/horse.mp3'}
                    type="audio/mpeg"
                  />
                  Your browser does not support HTML5 audio playback.
                </audio>
              </div>
            )}

            {type === 'document' && (
              <div className="evidence-modal__doc-wrapper">
                <FileText size={48} className="text-blue" />
                <span className="font-mono text-sm text-100 font-semibold">{description}</span>
                <span className="text-xs text-muted">Forensic Document Scan</span>
              </div>
            )}
          </div>
        </div>

        {/* ── Metadata Footer ── */}
        <div className="evidence-modal__footer">
          <div className="evidence-modal__meta">
            <div className="evidence-modal__meta-row">
              <span className="label-section text-xs">Description</span>
              <p className="text-sm text-100">{description}</p>
            </div>
            <div className="flex gap-6 margin-top-1">
              <div className="evidence-modal__meta-row">
                <span className="label-section text-xs">File Type</span>
                <span className="font-mono text-xs text-muted uppercase">{type}</span>
              </div>
              <div className="evidence-modal__meta-row">
                <span className="label-section text-xs">Upload Date</span>
                <span className="font-mono text-xs text-muted">{date}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
