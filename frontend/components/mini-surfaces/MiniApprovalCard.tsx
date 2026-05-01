import { Check } from "lucide-react";

export function MiniApprovalCard({ label, onApprove }: { label: string; onApprove: () => Promise<void> }) {
  return (
    <article className="mini-surface-card approval-mini">
      <header>
        <span className="eyebrow">MiniApprovalCard</span>
        <h2>{label}</h2>
      </header>
      <div className="mini-surface-actions">
        <button className="primary-button" onClick={() => void onApprove()}><Check size={14} /> {label}</button>
      </div>
    </article>
  );
}
