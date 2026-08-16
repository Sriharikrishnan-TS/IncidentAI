"use client";

import { useState } from "react";
import { Network, Maximize2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useGraph } from "@/hooks/useGraph";

export default function GraphsPage() {
  const { data, loading } = useGraph();
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-[600px]" />
      </div>
    );
  }

  if (!data) return null;

  const selectedNodeData = data.nodes.find((n) => n.id === selectedNode);
  const nodeConnections = data.edges.filter(
    (e) => e.source === selectedNode || e.target === selectedNode,
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
          Dependency Graph
        </h1>
        <p className="mt-2 text-slate-400">
          Visualize service dependencies and relationships
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Graph Visualization */}
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Network className="h-5 w-5" />
                Service Dependencies
              </CardTitle>
              <button className="rounded-lg bg-slate-800 p-2 text-slate-400 transition-colors hover:bg-slate-700 hover:text-slate-100">
                <Maximize2 className="h-4 w-4" />
              </button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Simplified Graph Visualization */}
            <div className="relative h-[500px] overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-6">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {data.nodes.slice(0, 24).map((node, idx) => (
                  <button
                    key={node.id}
                    onClick={() => setSelectedNode(node.id)}
                    className={`group relative rounded-lg border p-3 text-center transition-all hover:scale-105 ${
                      selectedNode === node.id
                        ? "border-blue-500 bg-blue-500/20 shadow-lg shadow-blue-500/20"
                        : node.type === "service"
                          ? "border-slate-700 bg-slate-800/50 hover:border-blue-500/50"
                          : node.type === "database"
                            ? "border-slate-700 bg-purple-500/10 hover:border-purple-500/50"
                            : "border-slate-700 bg-emerald-500/10 hover:border-emerald-500/50"
                    }`}
                  >
                    <div className="text-xs font-medium text-slate-300 truncate max-w-[180px] mx-auto" title={node.id}>
                      {node.id}
                    </div>
                    <Badge variant="outline" className="mt-2 text-[10px]">
                      {node.type}
                    </Badge>
                  </button>
                ))}
              </div>
            </div>

            {/* Legend */}
            <div className="mt-4 flex flex-wrap gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded border border-slate-700 bg-slate-800/50" />
                <span className="text-slate-400">Service</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded border border-slate-700 bg-purple-500/10" />
                <span className="text-slate-400">Database</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded border border-slate-700 bg-emerald-500/10" />
                <span className="text-slate-400">Library</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Node Details */}
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle>Node Details</CardTitle>
            <CardDescription>
              {selectedNode
                ? "Information about selected node"
                : "Select a node to view details"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedNodeData ? (
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-100">
                    {selectedNodeData.id}
                  </h3>
                  <Badge variant="outline" className="mt-2">
                    {selectedNodeData.type}
                  </Badge>
                </div>

                <div>
                  <h4 className="mb-2 text-sm font-medium text-slate-400">
                    Dependencies (
                    {
                      nodeConnections.filter((e) => e.source === selectedNode)
                        .length
                    }
                    )
                  </h4>
                  <div className="space-y-2">
                    {nodeConnections
                      .filter((e) => e.source === selectedNode)
                      .map((edge, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-800/50 p-2 text-sm"
                        >
                          <span className="text-slate-300">{edge.target}</span>
                          <Badge variant="outline" className="text-xs">
                            {edge.type || "depends_on"}
                          </Badge>
                        </div>
                      ))}
                    {nodeConnections.filter((e) => e.source === selectedNode)
                      .length === 0 && (
                      <p className="text-sm text-slate-500">
                        No outgoing dependencies
                      </p>
                    )}
                  </div>
                </div>

                <div>
                  <h4 className="mb-2 text-sm font-medium text-slate-400">
                    Dependents (
                    {
                      nodeConnections.filter((e) => e.target === selectedNode)
                        .length
                    }
                    )
                  </h4>
                  <div className="space-y-2">
                    {nodeConnections
                      .filter((e) => e.target === selectedNode)
                      .map((edge, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-800/50 p-2 text-sm"
                        >
                          <span className="text-slate-300">{edge.source}</span>
                          <Badge variant="outline" className="text-xs">
                            {edge.type || "depends_on"}
                          </Badge>
                        </div>
                      ))}
                    {nodeConnections.filter((e) => e.target === selectedNode)
                      .length === 0 && (
                      <p className="text-sm text-slate-500">
                        No incoming dependencies
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex h-64 items-center justify-center text-center text-sm text-slate-500">
                Click on a node in the graph to view its details and connections
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Stats */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="text-center">
              <p className="text-sm font-medium text-slate-400">Total Nodes</p>
              <p className="mt-2 text-3xl font-bold text-slate-100">
                {data.nodes.length}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="text-center">
              <p className="text-sm font-medium text-slate-400">Total Edges</p>
              <p className="mt-2 text-3xl font-bold text-slate-100">
                {data.edges.length}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="text-center">
              <p className="text-sm font-medium text-slate-400">Services</p>
              <p className="mt-2 text-3xl font-bold text-slate-100">
                {data.nodes.filter((n) => n.type === "service").length}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Made with Bob
