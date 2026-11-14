import Link from "next/link";
export default function NotFound() {
  return (
    <section className="page-heading">
      <h1>Page not found</h1>
      <p>This workspace page is unavailable.</p>
      <Link className="primary-link" href="/">
        Return to overview
      </Link>
    </section>
  );
}
