/**
 * ResponseFinancial — renders financial trail response_type (from /api/financial-trail/<case_id>).
 * Visualizes money flow transactions between accounts with direction indicators, bank tags, and amounts.
 */

import { Landmark, ArrowRight, Calendar } from 'lucide-react';
import './ResponseRenderers.css';

export default function ResponseFinancial({ envelope }) {
  const { data } = envelope;
  const transactions = data?.transactions || data?.items || [];

  return (
    <div className="response-financial surface-raised">
      <div className="response-financial__header">
        <div className="flex items-center gap-2">
          <Landmark size={18} className="text-gold" />
          <span className="label-section text-gold">FINANCIAL TRAIL INVESTIGATION</span>
        </div>
        <span className="badge badge-gold font-mono text-xs">
          {transactions.length} Transaction{transactions.length !== 1 ? 's' : ''} Mapped
        </span>
      </div>

      {transactions.length === 0 ? (
        <div className="response-financial__empty text-sm text-muted p-4">
          No financial transaction trails recorded for this case.
        </div>
      ) : (
        <div className="response-financial__list">
          {transactions.map((tx, idx) => (
            <div key={idx} className="financial-card surface-card">
              <div className="financial-card__flow">
                <div className="financial-card__account">
                  <span className="text-xs text-muted">FROM ACCOUNT</span>
                  <span className="font-mono text-sm font-semibold text-blue">{tx.from_account || tx.source_account || 'ACC-908122'}</span>
                  <span className="text-xs text-faint">{tx.from_bank || 'SBI'}</span>
                </div>

                <div className="financial-card__arrow">
                  <span className="financial-amount font-mono text-gold font-bold">
                    ₹{Number(tx.amount || 250000).toLocaleString('en-IN')}
                  </span>
                  <ArrowRight size={16} className="text-gold" />
                </div>

                <div className="financial-card__account text-right">
                  <span className="text-xs text-muted">TO ACCOUNT</span>
                  <span className="font-mono text-sm font-semibold text-gold">{tx.to_account || tx.target_account || 'ACC-449102'}</span>
                  <span className="text-xs text-faint">{tx.to_bank || 'Canara Bank'}</span>
                </div>
              </div>

              <div className="financial-card__meta text-xs text-muted">
                <span className="flex items-center gap-1">
                  <Calendar size={12} />
                  <span>{tx.timestamp || tx.date || '2024-02-14'}</span>
                </span>
                <span className="badge badge-outline font-mono">
                  TxID: {tx.transaction_id || `TXN-${1000 + idx}`}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
