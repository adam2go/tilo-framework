import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <main className="landing-page">
      <section className="landing-hero">
        <div className="landing-copy">
          <span className="eyebrow">Tilo Framework · ROAM Loop · Surface Protocol v1</span>
          <h1>AI-native SaaS agents that render interfaces, observe actions, act safely, and memorize learning.</h1>
          <p>
            Tilo is not a chatbot wrapper. It turns a conversation into a task, a run,
            a stream of focused surfaces, durable human decisions, and confirmed memory.
          </p>
          <div className="landing-actions">
            <Link className="primary-link" href="/demo">
              Open Demo
              <ArrowRight size={16} />
            </Link>
            <Link className="primary-link" href="/canvas" style={{ background: "linear-gradient(135deg, #6366f1, #a855f7)" }}>
              3D Canvas
              <ArrowRight size={16} />
            </Link>
            <a
              className="secondary-link"
              href="https://github.com/adam2go/tilo-framework"
              target="_blank"
              rel="noreferrer"
            >
              View GitHub
            </a>
          </div>
        </div>
        <div className="roam-preview" aria-label="ROAM product preview">
          {["Render", "Observe", "Act", "Memorize"].map((stage, index) => (
            <div className="preview-stage" key={stage}>
              <span>{index + 1}</span>
              <strong>{stage}</strong>
              <small>
                {stage === "Render" ? "SurfaceTurn" : null}
                {stage === "Observe" ? "UIInteractionEvent" : null}
                {stage === "Act" ? "Confirmation / Tool" : null}
                {stage === "Memorize" ? "Confirmed memory" : null}
              </small>
            </div>
          ))}
          <div className="preview-surface">
            <strong>Contract Review Surface</strong>
            <div className="preview-risk-row">
              <span>Liability</span>
              <em>high</em>
            </div>
            <div className="preview-risk-row">
              <span>Termination</span>
              <em>medium</em>
            </div>
            <button>Approve revision</button>
          </div>
        </div>
      </section>

      <section className="landing-section">
        <div>
          <span className="eyebrow">Why ROAM</span>
          <h2>Not a chat transcript. A generated workflow surface.</h2>
        </div>
        <div className="landing-explainer-grid">
          <ExplainerCard
            title="Render"
            detail="The agent renders only the surface needed for the next decision — one focused SurfaceTurn at a time."
          />
          <ExplainerCard
            title="Observe"
            detail="Every meaningful click becomes a durable UIInteractionEvent, Confirmation, Feedback, or Memory event."
          />
          <ExplainerCard
            title="Act"
            detail="Approved actions can update artifacts, invoke tools, continue tasks, or create confirmation-gated next steps."
          />
          <ExplainerCard
            title="Memorize"
            detail="Only reviewed learning — including patterns from your action stream — becomes long-term memory."
          />
        </div>
      </section>

      <section className="landing-section architecture-band">
        <div>
          <span className="eyebrow">Developer Architecture</span>
          <h2>Conversation {"->"} Task {"->"} Run {"->"} SurfaceTurn {"->"} Observation {"->"} Memory.</h2>
        </div>
        <p>
          Tilo keeps backend primitives explicit: Task, Run, TraceStep, SurfaceTurn,
          Artifact, Confirmation, UIInteractionEvent, Memory, Skill, and ToolInvocation.
        </p>
      </section>
    </main>
  );
}

function ExplainerCard({ title, detail }: { title: string; detail: string }) {
  return (
    <article className="explainer-card">
      <strong>{title}</strong>
      <span>{detail}</span>
    </article>
  );
}
