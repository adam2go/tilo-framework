import { Database } from "lucide-react";

export function MiniMemoryCard({
  content,
  labels,
  onMemory,
  onSkip,
}: {
  content: string;
  labels: { title: string; why: string; remember: string; editDirection: string; notNow: string };
  onMemory: () => Promise<void>;
  onSkip: () => Promise<void>;
}) {
  return (
    <article className="mini-surface-card memory-mini">
      <header>
        <span className="eyebrow">MiniMemoryCard</span>
        <h2>{labels.title}</h2>
      </header>
      <p>{content}</p>
      <small>{labels.why}</small>
      <div className="mini-surface-actions">
        <button className="primary-button" onClick={() => void onMemory()}><Database size={14} /> {labels.remember}</button>
        <button className="secondary-action">{labels.editDirection}</button>
        <button className="secondary-action" onClick={() => void onSkip()}>{labels.notNow}</button>
      </div>
    </article>
  );
}
