"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowDown, ArrowRight, Zap, Shield, Globe2, FileSearch } from "lucide-react";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { Particles } from "@/components/effects/Particles";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Message } from "@/types";
import toast from "react-hot-toast";

export function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollButton(!isAtBottom && messages.length > 0);
    };

    container.addEventListener("scroll", handleScroll);
    return () => container.removeEventListener("scroll", handleScroll);
  }, [messages.length]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSend = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    };

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);

    try {
      const response = await api.query(content, { top_k: 3 });

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id
            ? {
                ...msg,
                content: response.answer,
                sources: response.sources,
                isStreaming: false,
              }
            : msg
        )
      );
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to get response";

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id
            ? {
                ...msg,
                content: `❌ ${errorMessage}`,
                isStreaming: false,
                error: true,
              }
            : msg
        )
      );

      toast.error("Failed to get response");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full relative mesh-bg">
      <Particles count={15} />

      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto relative z-10"
      >
        <div className="max-w-4xl mx-auto p-4 md:p-6">
          <AnimatePresence mode="popLayout">
            {messages.length === 0 ? (
              <EmptyState onExampleClick={handleSend} />
            ) : (
              <div className="space-y-6">
                {messages.map((message, index) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    index={index}
                  />
                ))}
              </div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
      </div>

      <AnimatePresence>
        {showScrollButton && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-32 right-6 z-20"
          >
            <Button
              size="icon"
              onClick={scrollToBottom}
              className="h-10 w-10 rounded-full shadow-xl bg-gradient-to-br from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
            >
              <ArrowDown className="h-4 w-4 text-white" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}

function EmptyState({ onExampleClick }: { onExampleClick: (msg: string) => void }) {
  const stats = [
    { value: "10+", label: "Formats", icon: FileSearch },
    { value: "3", label: "Languages", icon: Globe2 },
    { value: "<2s", label: "Speed", icon: Zap },
    { value: "100%", label: "Private", icon: Shield },
  ];

  const examples = [
    { text: "What is RAG?", icon: "🤔", category: "Concept" },
    { text: "Summarize the documents", icon: "📝", category: "Summary" },
    { text: "List all key features", icon: "✨", category: "Analysis" },
    { text: "Translate to Hindi: Hello", icon: "🌐", category: "Translation" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)] text-center px-4 py-8"
    >
      {/* ───── LAUREL LOGO ───── */}
      <motion.div
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{
          type: "spring",
          stiffness: 200,
          damping: 15,
          delay: 0.2,
        }}
        className="relative mb-5"
      >
        <div className="absolute inset-0 -m-6 bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-blue-500/20 blur-3xl rounded-full" />
        
        <svg viewBox="0 0 100 100" className="w-16 h-16 relative" fill="none">
          <path
            d="M50 15 Q35 25, 30 40 Q28 50, 35 58"
            stroke="url(#laurelGrad)"
            strokeWidth="2.5"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d="M50 15 Q65 25, 70 40 Q72 50, 65 58"
            stroke="url(#laurelGrad)"
            strokeWidth="2.5"
            strokeLinecap="round"
            fill="none"
          />
          <ellipse cx="35" cy="30" rx="4" ry="7" fill="url(#leafGrad)" transform="rotate(-30 35 30)" />
          <ellipse cx="30" cy="40" rx="4" ry="7" fill="url(#leafGrad)" transform="rotate(-45 30 40)" />
          <ellipse cx="30" cy="50" rx="4" ry="7" fill="url(#leafGrad)" transform="rotate(-60 30 50)" />
          <ellipse cx="65" cy="30" rx="4" ry="7" fill="url(#leafGrad)" transform="rotate(30 65 30)" />
          <ellipse cx="70" cy="40" rx="4" ry="7" fill="url(#leafGrad)" transform="rotate(45 70 40)" />
          <ellipse cx="70" cy="50" rx="4" ry="7" fill="url(#leafGrad)" transform="rotate(60 70 50)" />
          <line x1="50" y1="58" x2="50" y2="85" stroke="url(#laurelGrad)" strokeWidth="2.5" strokeLinecap="round" />
          <circle cx="50" cy="15" r="3" fill="url(#leafGrad)" />
          
          <defs>
            <linearGradient id="laurelGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#a855f7" />
              <stop offset="50%" stopColor="#ec4899" />
              <stop offset="100%" stopColor="#3b82f6" />
            </linearGradient>
            <linearGradient id="leafGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#c084fc" />
              <stop offset="100%" stopColor="#60a5fa" />
            </linearGradient>
          </defs>
        </svg>
      </motion.div>

      {/* ───── TITLE (Smaller, balanced) ───── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-2"
      >
        <h1 className="font-serif text-4xl md:text-5xl font-medium tracking-tight gradient-text leading-tight">
          RAG Assistant
        </h1>
      </motion.div>

      {/* ───── METADATA (Single line) ───── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="flex items-center gap-2 text-xs text-muted-foreground mb-6"
      >
        <span>by The Intelligence Co.</span>
        <span className="w-1 h-1 rounded-full bg-muted-foreground/40" />
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-emerald-400 font-medium">Production Ready</span>
        </div>
      </motion.div>

      {/* ───── MAIN QUESTION ───── */}
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="font-serif text-xl md:text-2xl text-foreground/90 mb-8 max-w-xl italic"
      >
        What document do you want to chat with today?
      </motion.h2>

      {/* ───── STATS (Compact) ───── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="grid grid-cols-4 gap-2 mb-8 w-full max-w-md"
      >
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.7 + idx * 0.05 }}
              className="glass rounded-xl p-3 border border-border/40 hover:border-primary/30 transition-all group text-center"
            >
              <Icon className="w-3.5 h-3.5 text-muted-foreground mb-1.5 group-hover:text-primary transition-colors mx-auto" />
              <div className="font-serif text-xl font-semibold gradient-text leading-none">
                {stat.value}
              </div>
              <div className="text-[9px] text-muted-foreground uppercase tracking-widest mt-1">
                {stat.label}
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* ───── EXAMPLES ───── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="w-full max-w-2xl mb-6"
      >
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="h-px w-8 bg-gradient-to-r from-transparent to-border" />
          <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">
            Try asking
          </p>
          <div className="h-px w-8 bg-gradient-to-l from-transparent to-border" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {examples.map((example, idx) => (
            <motion.button
              key={example.text}
              initial={{ opacity: 0, x: idx % 2 === 0 ? -20 : 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.9 + idx * 0.08 }}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onExampleClick(example.text)}
              className="group relative p-3.5 text-left rounded-xl border border-border/40 glass hover:border-primary/50 transition-all overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/0 via-pink-500/0 to-blue-500/0 group-hover:from-purple-500/5 group-hover:via-pink-500/5 group-hover:to-blue-500/5 transition-all" />

              <div className="relative">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[9px] uppercase tracking-widest text-muted-foreground/70 font-bold">
                    {example.category}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                </div>

                <div className="flex items-center gap-2.5">
                  <span className="text-xl">{example.icon}</span>
                  <span className="text-sm font-medium flex-1 text-foreground/90">
                    {example.text}
                  </span>
                </div>
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* ───── TECH PILLS (Compact) ───── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2 }}
        className="w-full max-w-2xl"
      >
        <div className="flex flex-wrap items-center justify-center gap-1.5">
          {[
            { name: "Qwen 2.5", color: "border-emerald-500/30 text-emerald-300 bg-emerald-500/10" },
            { name: "BGE-M3", color: "border-amber-500/30 text-amber-300 bg-amber-500/10" },
            { name: "pgvector", color: "border-blue-500/30 text-blue-300 bg-blue-500/10" },
            { name: "FastAPI", color: "border-purple-500/30 text-purple-300 bg-purple-500/10" },
          ].map((tech, idx) => (
            <motion.div
              key={tech.name}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 1.3 + idx * 0.05 }}
              whileHover={{ scale: 1.05, y: -1 }}
              className={`px-3 py-1 rounded-full border backdrop-blur-md text-[11px] font-semibold ${tech.color}`}
            >
              {tech.name}
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}