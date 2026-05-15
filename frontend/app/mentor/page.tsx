"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, MessageSquare, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { BentoCard, BentoCardHeader, BentoCardContent, MentorCard } from "@/components/bento";
import { mockMentorQuery } from "@/services/mockData";
import type { ChatMessage, MentorQueryResponse } from "@/types/api";

const SUGGESTED_QUESTIONS = [
  "What should I learn first?",
  "Which service has the most dependencies?",
  "How can I improve test coverage?",
  "What caused the recent incidents?",
];

interface ExtendedChatMessage extends ChatMessage {
  confidence?: number;
  sources?: string[];
}

export default function MentorPage() {
  const [messages, setMessages] = useState<ExtendedChatMessage[]>([
    {
      id: "1",
      sender: "ai",
      message:
        "Hello! I'm your AI mentor. I can help you understand your codebase, suggest improvements, and answer questions about your services. What would you like to know?",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: "user",
      message: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const repoId = localStorage.getItem("current_repo_id") || "demo_repo";
      const response = await mockMentorQuery(repoId, input);

      const aiMessage: ExtendedChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        message: response.answer,
        timestamp: new Date().toISOString(),
        confidence: response.confidence,
        sources: response.sources,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage: ExtendedChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        message: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
          AI Mentor
        </h1>
        <p className="mt-2 text-slate-400">
          Get personalized guidance and insights about your codebase
        </p>
      </motion.div>

      {/* Chat Container - Bento Style */}
      <BentoCard gradient glow>
        <BentoCardHeader
          title="Chat with Mentor"
          icon={<MessageSquare className="h-5 w-5 text-purple-400" />}
        />
        <BentoCardContent className="p-0">
          {/* Messages */}
          <div className="h-[500px] overflow-y-auto p-6 space-y-4">
            {messages.map((message, idx) => (
              <MentorCard
                key={message.id}
                message={message.message}
                sender={message.sender}
                confidence={message.confidence}
                sources={message.sources}
                index={idx}
              />
            ))}
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-3"
              >
                <div className="rounded-lg bg-purple-500/10 p-2 ring-1 ring-purple-500/30">
                  <Sparkles className="h-5 w-5 text-purple-400" />
                </div>
                <div className="flex-1 rounded-lg border border-slate-800 bg-slate-800/50 p-4 backdrop-blur-sm">
                  <div className="flex items-center gap-2 text-slate-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Questions */}
          {messages.length === 1 && (
            <div className="border-t border-slate-800 p-4 bg-slate-900/30">
              <p className="mb-3 text-sm font-medium text-slate-400">
                Suggested questions:
              </p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_QUESTIONS.map((question, idx) => (
                  <motion.button
                    key={question}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: idx * 0.1 }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleSuggestedQuestion(question)}
                    className="rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-sm text-slate-300 transition-all hover:border-purple-500/50 hover:bg-slate-800 hover:text-slate-100"
                  >
                    {question}
                  </motion.button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="border-t border-slate-800 p-4 bg-slate-900/30">
            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about your codebase..."
                className="flex-1 resize-none rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20 transition-all backdrop-blur-sm"
                rows={2}
                disabled={loading}
              />
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  onClick={handleSend}
                  disabled={loading || !input.trim()}
                  className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 shadow-lg shadow-purple-500/20"
                >
                  <Send className="h-5 w-5" />
                </Button>
              </motion.div>
            </div>
          </div>
        </BentoCardContent>
      </BentoCard>
    </div>
  );
}

// Made with Bob
