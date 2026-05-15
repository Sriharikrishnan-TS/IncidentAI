"use client";

import { useState } from "react";
import { Upload, Loader2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { mockUploadRepo } from "@/services/mockData";
import { useRouter } from "next/navigation";

export default function UploadPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleUpload = async () => {
    if (!repoUrl.trim()) {
      setError("Please enter a repository URL");
      return;
    }

    setUploading(true);
    setError("");

    try {
      const result = await mockUploadRepo(repoUrl);
      // Store repo_id in localStorage for demo purposes
      localStorage.setItem("current_repo_id", result.repo_id);
      // Navigate to dashboard
      router.push("/dashboard");
    } catch (err) {
      setError("Failed to upload repository. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
          Upload Repository
        </h1>
        <p className="mt-2 text-slate-400">
          Connect your GitHub repository to start analyzing your codebase
        </p>
      </div>

      <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            GitHub Repository
          </CardTitle>
          <CardDescription>
            Enter your repository URL to begin the analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* URL Input */}
          <div className="space-y-2">
            <label
              htmlFor="repo-url"
              className="text-sm font-medium text-slate-300"
            >
              Repository URL
            </label>
            <input
              id="repo-url"
              type="text"
              placeholder="https://github.com/username/repository"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              disabled={uploading}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Upload Button */}
          <Button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-medium py-6"
          >
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Uploading Repository...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-5 w-5" />
                Upload Repository
              </>
            )}
          </Button>

          {/* Info */}
          <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 p-4 text-sm text-blue-300">
            <p className="font-medium mb-1">What happens next?</p>
            <ul className="space-y-1 text-blue-300/80">
              <li>• Repository structure will be analyzed</li>
              <li>• Dependencies will be mapped</li>
              <li>• Fragility scores will be calculated</li>
              <li>• AI mentor will be ready to help</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Example Repositories */}
      <Card className="border-slate-800 bg-slate-900/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-lg">Example Repositories</CardTitle>
          <CardDescription>
            Try these sample repositories to explore the platform
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[
              "https://github.com/vercel/next.js",
              "https://github.com/facebook/react",
              "https://github.com/microsoft/vscode",
            ].map((url) => (
              <button
                key={url}
                onClick={() => setRepoUrl(url)}
                className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 text-left text-sm text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-800"
                disabled={uploading}
              >
                {url}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Made with Bob
