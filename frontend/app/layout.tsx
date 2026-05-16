import "./globals.css";
import type { ReactNode } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";

export const metadata = {
  title: "IncidentOS - Engineering Intelligence Platform",
  description: "AI-powered engineering intelligence for incident prevention and analysis",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Sidebar />
        <Navbar />
        <main className="ml-64 mt-16 min-h-screen bg-slate-950 p-6">
          {children}
        </main>
      </body>
    </html>
  );
}
