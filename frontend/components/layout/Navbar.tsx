"use client";

import { Bell, Settings, User } from "lucide-react";

export function Navbar() {
  return (
    <header className="fixed left-64 right-0 top-0 z-30 h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="flex h-full items-center justify-between px-6">
        {/* Left side - could add breadcrumbs or search */}
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold text-slate-100">
            Engineering Intelligence Platform
          </h1>
        </div>

        {/* Right side - actions */}
        <div className="flex items-center gap-3">
          <button className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-100">
            <Bell className="h-5 w-5" />
          </button>
          <button className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-100">
            <Settings className="h-5 w-5" />
          </button>
          <button className="flex items-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-slate-100 transition-colors hover:bg-slate-700">
            <User className="h-4 w-4" />
            <span>Developer</span>
          </button>
        </div>
      </div>
    </header>
  );
}

// Made with Bob
