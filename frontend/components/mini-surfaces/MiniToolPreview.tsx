export function MiniToolPreview({ body, title }: { body: string; title: string }) {
  return (
    <article className="mini-surface-card tool-mini">
      <header>
        <span className="eyebrow">MiniToolPreview</span>
        <h2>{title}</h2>
      </header>
      <p>{body}</p>
    </article>
  );
}
