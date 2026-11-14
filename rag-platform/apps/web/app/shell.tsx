"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { navigation } from "./navigation";

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const current = navigation.find((item) => item.href === pathname);
  return (
    <div className="workspace">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside className="sidebar" aria-label="Workspace">
        <Link className="brand" href="/" aria-label="RAG Platform home">
          <span className="brand-mark" aria-hidden="true">
            R
          </span>
          <span>
            RAG Platform<small>Connected knowledge</small>
          </span>
        </Link>
        <div className="sidebar-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={pathname === item.href ? "page" : undefined}
            >
              <span aria-hidden="true">{item.mark}</span>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="status-dot" aria-hidden="true" /> Development
          workspace
          <p>Source connections and answers are not available yet.</p>
        </div>
      </aside>
      <div className="content">
        <header className="topbar">
          <span>{current?.label ?? "Workspace"}</span>
          <span className="badge">Development preview</span>
        </header>
        <main id="main" className="main" tabIndex={-1}>
          {children}
        </main>
        <footer>
          RAG Platform
          <span>Access stays explicit. Evidence stays traceable.</span>
        </footer>
      </div>
    </div>
  );
}
