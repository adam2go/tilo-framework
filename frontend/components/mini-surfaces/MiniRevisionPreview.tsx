import { ArrowUpRight } from "lucide-react";

export function MiniRevisionPreview({
  after,
  before,
  labels,
  onFullReview,
  title,
}: {
  after: string;
  before: string;
  labels: { before: string; after: string; makeSofter: string; makeStricter: string; draftEmail: string; openArtifact: string };
  onFullReview: () => Promise<void>;
  title: string;
}) {
  return (
    <article className="mini-surface-card revision-mini">
      <header>
        <span className="eyebrow">MiniRevisionPreview</span>
        <h2>{title}</h2>
      </header>
      <div className="mini-before-after">
        <div><span>{labels.before}</span><p>{before}</p></div>
        <div><span>{labels.after}</span><p>{after}</p></div>
      </div>
      <div className="mini-surface-actions">
        <button className="secondary-action">{labels.makeSofter}</button>
        <button className="secondary-action">{labels.makeStricter}</button>
        <button className="secondary-action">{labels.draftEmail}</button>
        <button className="secondary-action" onClick={() => void onFullReview()}><ArrowUpRight size={14} /> {labels.openArtifact}</button>
      </div>
    </article>
  );
}
