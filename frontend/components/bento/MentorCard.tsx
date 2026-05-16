"use client";

import { motion } from "framer-motion";
import { Sparkles, User, Bot } from "lucide-react";
import { BentoCard, BentoCardContent } from "./BentoCard";

interface MentorCardProps {
  message: string;
  sender: "user" | "ai";
  confidence?: number;
  sources?: string[];
  index?: number;
}

export function MentorCard({
  message,
  sender,
  confidence,
  sources,
  index = 0,
}: MentorCardProps) {
  const isAI = sender === "ai";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      className={isAI ? "" : "ml-auto max-w-[80%]"}
    >
      <BentoCard
        className={
          isAI
            ? "bg-gradient-to-br from-purple-500/10 via-blue-500/5 to-transparent border-purple-500/20"
            : "bg-gradient-to-br from-slate-800/80 to-slate-900/50 border-slate-700"
        }
        hover={false}
      >
        <BentoCardContent className="py-4">
          <div className="flex items-start gap-3">
            {/* Avatar */}
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: index * 0.1 + 0.2, type: "spring" }}
              className={`rounded-lg p-2 ring-1 ${
                isAI
                  ? "bg-purple-500/10 ring-purple-500/30"
                  : "bg-slate-700/50 ring-slate-600/50"
              }`}
            >
              {isAI ? (
                <Bot className="h-5 w-5 text-purple-400" />
              ) : (
                <User className="h-5 w-5 text-slate-400" />
              )}
            </motion.div>

            {/* Content */}
            <div className="flex-1 space-y-3">
              <p className="text-sm leading-relaxed text-slate-200">
                {message}
              </p>

              {/* AI-specific metadata */}
              {isAI && (
                <div className="space-y-2">
                  {confidence !== undefined && (
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-3 w-3 text-purple-400" />
                      <span className="text-xs text-slate-400">
                        Confidence: {(confidence * 100).toFixed(0)}%
                      </span>
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-800">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${confidence * 100}%` }}
                          transition={{
                            delay: index * 0.1 + 0.4,
                            duration: 0.8,
                          }}
                          className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
                        />
                      </div>
                    </div>
                  )}

                  {sources && sources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {sources.map((source, idx) => (
                        <motion.span
                          key={source}
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: index * 0.1 + 0.5 + idx * 0.05 }}
                          className="rounded-md bg-slate-800/50 px-2 py-0.5 text-xs text-slate-400 ring-1 ring-slate-700/50"
                        >
                          {source}
                        </motion.span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </BentoCardContent>
      </BentoCard>
    </motion.div>
  );
}

// Made with Bob
