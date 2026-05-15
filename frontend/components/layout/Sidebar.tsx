"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Upload,
  LayoutDashboard,
  AlertTriangle,
  Network,
  MessageSquare,
  Search,
  GitBranch,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Upload", href: "/upload", icon: Upload },
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Fragility", href: "/fragility", icon: AlertTriangle },
  { name: "Graphs", href: "/graphs", icon: Network },
  { name: "Mentor", href: "/mentor", icon: MessageSquare },
  { name: "Investigation", href: "/investigation", icon: Search },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-slate-800 bg-slate-950">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center gap-2 border-b border-slate-800 px-6">
          <GitBranch className="h-6 w-6 text-blue-500" />
          <span className="text-xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
            IncidentOS
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                  isActive
                    ? "bg-slate-800 text-slate-100 shadow-lg shadow-blue-500/10"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-100",
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="border-t border-slate-800 p-4">
          <div className="rounded-lg bg-slate-800/50 p-3 text-xs text-slate-400">
            <p className="font-medium text-slate-300">
              AI-Powered Intelligence
            </p>
            <p className="mt-1">Analyze, predict, and prevent incidents</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

// Made with Bob
