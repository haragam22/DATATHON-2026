/**
 * PDFExportButton — Milestone 11: PDF Conversation Export.
 *
 * GET /api/conversation/<session_id>/export
 * Returns raw application/pdf bytes.
 */

import { useState } from 'react';
import { Download, Loader, CheckCircle, AlertTriangle } from 'lucide-react';
import { exportConversation, ApiError } from '../../services/api';
import './PDFExportButton.css';

export default function PDFExportButton({ sessionId, className = '' }) {
  const [isExporting, setIsExporting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const handleExport = async () => {
    if (!sessionId || isExporting) return;

    setIsExporting(true);
    setError(null);
    setSuccess(false);

    try {
      const blob = await exportConversation(sessionId);

      // Create blob download URL
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ksp_conversation_${sessionId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('PDF export failed:', err);
      setError(err instanceof ApiError ? err.message : 'Export failed');
      setTimeout(() => setError(null), 4000);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <button
      className={`btn btn-ghost pdf-export-btn font-mono text-xs ${className}`}
      onClick={handleExport}
      disabled={!sessionId || isExporting}
      title="Export conversation history as official PDF file"
    >
      {isExporting ? (
        <>
          <Loader size={14} className="spin text-blue" />
          <span>Generating PDF…</span>
        </>
      ) : success ? (
        <>
          <CheckCircle size={14} className="text-green" />
          <span className="text-green">Exported PDF!</span>
        </>
      ) : error ? (
        <>
          <AlertTriangle size={14} className="text-red" />
          <span className="text-red">Error</span>
        </>
      ) : (
        <>
          <Download size={14} className="text-gold" />
          <span>Export PDF</span>
        </>
      )}
    </button>
  );
}
