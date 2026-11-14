import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { isSection, sections } from "../sections";
import { StatePanel } from "../state-panel";

type Props = { params: Promise<{ section: string }> };
export function generateStaticParams() {
  return Object.keys(sections).map((section) => ({ section }));
}
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { section } = await params;
  return {
    title: `${isSection(section) ? sections[section].title : "Not found"} | RAG Platform`,
  };
}
export default async function SectionPage({ params }: Props) {
  const { section } = await params;
  if (!isSection(section)) notFound();
  const view = sections[section];
  return (
    <>
      <header className="page-heading">
        <span className="eyebrow">YOUR WORKSPACE</span>
        <h1>{view.title}</h1>
        <p>{view.description}</p>
      </header>
      <StatePanel state="empty" title={view.emptyTitle}>
        <p>{view.emptyText}</p>
        <Link className="primary-link" href={view.nextHref}>
          {view.nextLabel}
          <span aria-hidden="true">→</span>
        </Link>
      </StatePanel>
      <section className="card-grid" aria-label="Capabilities and availability">
        {view.cards.map((card) => (
          <article className="step-card" key={card.title}>
            <h2>{card.title}</h2>
            <p>{card.text}</p>
          </article>
        ))}
      </section>
    </>
  );
}
