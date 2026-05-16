/**
 * useMentor Hook
 *
 * Manages AI mentor query operations and chat state
 */

import { useState, useCallback } from "react";
import { queryMentor } from "@/services/mentorService";
import type { ChatMessage, MentorQueryResponse } from "@/types/api";

interface ExtendedChatMessage extends ChatMessage {
  confidence?: number;
  sources?: string[];
}

interface UseMentorOptions {
  repo_id?: string;
  initialMessages?: ExtendedChatMessage[];
}

interface UseMentorReturn {
  messages: ExtendedChatMessage[];
  loading: boolean;
  error: string | null;
  sendMessage: (message: string) => Promise<void>;
  clearMessages: () => void;
}

/**
 * Hook for managing AI mentor interactions
 */
export function useMentor(options: UseMentorOptions = {}): UseMentorReturn {
  const {
    repo_id = typeof window !== "undefined"
      ? localStorage.getItem("current_repo_id") || "demo_repo"
      : "demo_repo",
    initialMessages = [
      {
        id: "1",
        sender: "ai" as const,
        message:
          "Hello! I'm your AI mentor. I can help you understand your codebase, suggest improvements, and answer questions about your services. What would you like to know?",
        timestamp: new Date().toISOString(),
      },
    ],
  } = options;

  const [messages, setMessages] =
    useState<ExtendedChatMessage[]>(initialMessages);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim() || loading) return;

      const userMessage: ExtendedChatMessage = {
        id: Date.now().toString(),
        sender: "user",
        message,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);
      setError(null);

      try {
        const response: MentorQueryResponse = await queryMentor(
          repo_id,
          message,
        );

        const aiMessage: ExtendedChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: "ai",
          message: response.answer,
          timestamp: new Date().toISOString(),
          confidence: response.confidence,
          sources: response.sources,
        };

        setMessages((prev) => [...prev, aiMessage]);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to get response";
        setError(errorMessage);

        const errorAiMessage: ExtendedChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: "ai",
          message: "Sorry, I encountered an error. Please try again.",
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, errorAiMessage]);
        console.error("[useMentor] Error:", err);
      } finally {
        setLoading(false);
      }
    },
    [repo_id, loading],
  );

  const clearMessages = useCallback(() => {
    setMessages(initialMessages);
    setError(null);
  }, [initialMessages]);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearMessages,
  };
}

// Made with Bob
