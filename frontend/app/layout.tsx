import "./globals.css";
import Link from "next/link";
import type { ReactNode } from "react";

const nav = [
  "upload",
  "dashboard",
  "mentor",
  "graphs",
  "fragility",
  "investigation",
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-slate-800 p-4">
          <nav className="flex flex-wrap gap-3 text-sm">
            {nav.map((path) => (
              <Link key={path} href={`/${path}`} className="rounded border border-slate-700 px-2 py-1">
                {path}
              </Link>
            ))}
          </nav>
        </header>
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
