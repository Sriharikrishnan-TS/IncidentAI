// Utility functions for styling and colors

export function getScoreColor(score: number): string {
  if (score >= 9) return "text-red-500";
  if (score >= 7) return "text-orange-500";
  if (score >= 4) return "text-yellow-500";
  return "text-emerald-500";
}

export function getScoreBgColor(score: number): string {
  if (score >= 9) return "bg-red-500/10 border-red-500/20";
  if (score >= 7) return "bg-orange-500/10 border-orange-500/20";
  if (score >= 4) return "bg-yellow-500/10 border-yellow-500/20";
  return "bg-emerald-500/10 border-emerald-500/20";
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "bg-red-500 text-white";
    case "high":
      return "bg-orange-500 text-white";
    case "medium":
      return "bg-yellow-500 text-slate-900";
    case "low":
      return "bg-blue-500 text-white";
    default:
      return "bg-slate-500 text-white";
  }
}

export function getSeverityBorderColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "border-red-500/50";
    case "high":
      return "border-orange-500/50";
    case "medium":
      return "border-yellow-500/50";
    case "low":
      return "border-blue-500/50";
    default:
      return "border-slate-500/50";
  }
}

export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;

  return date.toLocaleDateString();
}

// Made with Bob
