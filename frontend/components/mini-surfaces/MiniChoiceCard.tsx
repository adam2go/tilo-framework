import { ArrowUpRight } from "lucide-react";

export function MiniChoiceCard({
  body,
  labels,
  onFullReview,
  title,
}: {
  body: string;
  labels: { makeSofter: string; makeStricter: string; openArtifact: string };
  onFullReview: () => Promise<void>;
  title: string;
}) {
  return (
    <article className="mini-surface-card choice-mini">
      <header>
        <span className="eyebrow">MiniChoiceCard</span>
        <h2>{title}</h2>
      </header>
      <p>{body}</p>
      <div className="mini-surface-actions">
        <button className="secondary-action">{labels.makeSofter}</button>
        <button className="secondary-action">{labels.makeStricter}</button>
        <button className="secondary-action" onClick={() => void onFullReview()}><ArrowUpRight size={14} /> {labels.openArtifact}</button>
      </div>
    </article>
  );
}
