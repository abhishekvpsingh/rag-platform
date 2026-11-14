import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { Shell } from "./shell";

export const metadata: Metadata = {
  title: "RAG Platform | Connected knowledge",
  description:
    "A workspace for current, permission-aware answers with traceable evidence.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
