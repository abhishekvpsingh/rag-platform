import Link from "next/link";

const steps = [
  {
    number: "01",
    title: "Connect your knowledge",
    text: "Bring Google Drive and OneDrive into one permission-aware workspace.",
    status: "Planned",
  },
  {
    number: "02",
    title: "Keep the right context",
    text: "Preserve document history, effective dates, and the scope of each policy.",
    status: "Planned",
  },
  {
    number: "03",
    title: "Ask with evidence",
    text: "Get concise answers with sources you can inspect and trust.",
    status: "Planned",
  },
];

export default function Home() {
  return (
    <div className="workspace">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside className="sidebar" aria-label="Workspace information">
        <Link className="brand" href="/" aria-label="RAG Platform home">
          <span className="brand-mark" aria-hidden="true">
            R
          </span>
          <span>
            RAG Platform<small>Connected knowledge</small>
          </span>
        </Link>
        <div className="sidebar-label">WORKSPACE</div>
        <div className="current-view">
          <span aria-hidden="true">◈</span> Overview
        </div>
        <div className="sidebar-note">
          <span className="status-dot" aria-hidden="true" /> Single-node
          foundation
          <p>Your workspace starts here. Source connections are coming next.</p>
        </div>
      </aside>
      <main id="main" className="main" tabIndex={-1}>
        <header className="topbar">
          <span>Workspace overview</span>
          <span className="badge">Development preview</span>
        </header>
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <span className="eyebrow">KNOWLEDGE, WITH CONTEXT</span>
            <h1 id="hero-title">
              Your company’s knowledge.
              <br />
              <span>A clearer answer.</span>
            </h1>
            <p>
              A connected workspace for finding what matters, understanding
              what’s current, and following the evidence.
            </p>
            <a className="primary-link" href="#getting-started">
              Explore the roadmap <span aria-hidden="true">→</span>
            </a>
          </div>
          <div className="knowledge-art" aria-hidden="true">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="core">
              R<span>Knowledge</span>
            </div>
            <div className="satellite sat-one">Documents</div>
            <div className="satellite sat-two">Context</div>
            <div className="satellite sat-three">Evidence</div>
          </div>
        </section>
        <section className="notice" aria-label="Implementation status">
          <span className="notice-icon" aria-hidden="true">
            i
          </span>
          <div>
            <strong>A foundation, ready to build on</strong>
            <p>
              This is a development preview. No storage accounts are connected,
              and document indexing and question answering are not available
              yet.
            </p>
          </div>
        </section>
        <section id="getting-started" aria-labelledby="steps-title">
          <div className="section-heading">
            <div>
              <span className="eyebrow">THE PATH AHEAD</span>
              <h2 id="steps-title">From scattered files to grounded answers</h2>
            </div>
            <span className="muted">Built one verified step at a time</span>
          </div>
          <div className="steps">
            {steps.map((step) => (
              <article className="step-card" key={step.number}>
                <div className="card-top">
                  <span className="step-number">{step.number}</span>
                  <span className="planned">{step.status}</span>
                </div>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </article>
            ))}
          </div>
        </section>
        <section className="principles" aria-label="Design principles">
          <p>
            <span aria-hidden="true">◇</span> Access stays explicit
          </p>
          <p>
            <span aria-hidden="true">◷</span> Current and historical context
          </p>
          <p>
            <span aria-hidden="true">→</span> Evidence you can inspect
          </p>
        </section>
        <footer>
          RAG Platform{" "}
          <span>Single-node first. Built for what comes next.</span>
        </footer>
      </main>
    </div>
  );
}
