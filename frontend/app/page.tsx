"use client";

import Link from "next/link";
import {
  Upload,
  LayoutDashboard,
  AlertTriangle,
  Network,
  MessageSquare,
  Search,
  ArrowRight,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const features = [
  {
    icon: Upload,
    title: "Upload Repository",
    description:
      "Connect your GitHub repository to start analyzing your codebase",
    href: "/upload",
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: LayoutDashboard,
    title: "Dashboard",
    description:
      "Get an overview of your repository health and recent incidents",
    href: "/dashboard",
    color: "from-purple-500 to-pink-500",
  },
  {
    icon: AlertTriangle,
    title: "Fragility Analysis",
    description:
      "Identify services that need attention based on fragility scores",
    href: "/fragility",
    color: "from-orange-500 to-red-500",
  },
  {
    icon: Network,
    title: "Dependency Graph",
    description: "Visualize service dependencies and relationships",
    href: "/graphs",
    color: "from-emerald-500 to-teal-500",
  },
  {
    icon: MessageSquare,
    title: "AI Mentor",
    description: "Get personalized guidance and insights about your codebase",
    href: "/mentor",
    color: "from-violet-500 to-purple-500",
  },
  {
    icon: Search,
    title: "Investigation",
    description: "AI-powered root cause analysis for your incidents",
    href: "/investigation",
    color: "from-pink-500 to-rose-500",
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto max-w-6xl space-y-12">
      {/* Hero Section */}
      <div className="text-center space-y-4 py-12">
        <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
          IncidentOS
        </h1>
        <p className="text-xl text-slate-300 max-w-2xl mx-auto">
          AI-Powered Engineering Intelligence Platform
        </p>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Analyze your codebase, predict incidents, and get personalized
          guidance from our AI mentor. Built for modern engineering teams.
        </p>
        <div className="flex gap-4 justify-center pt-4">
          <Link
            href="/upload"
            className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 px-6 py-3 font-medium text-white transition-transform hover:scale-105"
          >
            Get Started
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-6 py-3 font-medium text-slate-100 transition-colors hover:bg-slate-700"
          >
            View Demo
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div>
        <h2 className="text-2xl font-bold text-slate-100 mb-6">Features</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <Link key={feature.href} href={feature.href}>
              <Card className="group border-slate-800 bg-slate-900/50 backdrop-blur-sm transition-all hover:scale-105 hover:border-slate-700 cursor-pointer h-full">
                <CardHeader>
                  <div
                    className={`inline-flex w-fit rounded-lg bg-gradient-to-br ${feature.color} p-3 mb-2`}
                  >
                    <feature.icon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                  <CardDescription className="text-slate-400">
                    {feature.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-sm text-blue-400 group-hover:gap-3 transition-all">
                    Learn more
                    <ArrowRight className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card className="border-slate-800 bg-gradient-to-br from-blue-500/10 to-purple-500/10 backdrop-blur-sm">
          <CardContent className="p-6 text-center">
            <p className="text-4xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
              AI-Powered
            </p>
            <p className="mt-2 text-sm text-slate-400">
              Advanced machine learning for incident prediction
            </p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-sm">
          <CardContent className="p-6 text-center">
            <p className="text-4xl font-bold bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
              Real-time
            </p>
            <p className="mt-2 text-sm text-slate-400">
              Continuous monitoring and analysis
            </p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-gradient-to-br from-pink-500/10 to-red-500/10 backdrop-blur-sm">
          <CardContent className="p-6 text-center">
            <p className="text-4xl font-bold bg-gradient-to-r from-pink-500 to-red-500 bg-clip-text text-transparent">
              Actionable
            </p>
            <p className="mt-2 text-sm text-slate-400">
              Clear recommendations and insights
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Made with Bob
