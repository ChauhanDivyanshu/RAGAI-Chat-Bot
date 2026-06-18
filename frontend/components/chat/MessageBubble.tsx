"use client";

import { motion } from "framer-motion";
import { Bot, User, FileText, Clock, Sparkles, Copy, Check, Zap } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { Message } from "@/types";
import toast from "react-hot-toast";

interface MessageBubbleProps {
  message: Message;
  index: number;
}

export function MessageBubble({ message, index }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    toast.success("Copied!", { icon: "📋" });
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ 
        duration: 0.3, 
        delay: index * 0.03,
        ease: [0.16, 1, 0.3, 1] 
      }}
      className={cn(
        "flex gap-2.5 w-full group",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* ───── AVATAR (Compact) ───── */}
      <div className="relative shrink-0">
        <div className={cn(
          "flex h-7 w-7 items-center justify-center rounded-lg shadow-sm",
          isUser
            ? "bg-gradient-to-br from-blue-500 to-indigo-600"
            : "bg-gradient-to-br from-purple-500 via-pink-500 to-indigo-500"
        )}>
          {isUser ? (
            <User className="h-3.5 w-3.5 text-white" />
          ) : (
            <Bot className="h-3.5 w-3.5 text-white" />
          )}
        </div>
      </div>

      {/* ───── CONTENT ───── */}
      <div className={cn(
        "flex flex-col gap-1 max-w-[80%] sm:max-w-[70%]",
        isUser ? "items-end" : "items-start"
      )}>
        {/* Message bubble */}
        <div
          className={cn(
            "relative px-3.5 py-2 rounded-xl border backdrop-blur-sm",
            isUser
              ? "bg-gradient-to-br from-blue-500 to-indigo-600 text-white border-blue-400/30"
              : message.error
              ? "bg-destructive/10 border-destructive/20 text-foreground"
              : "glass border-border/50 text-foreground"
          )}
        >
          {/* Copy button (only for AI) */}
          {!isUser && message.content && !message.isStreaming && (
            <motion.button
              whileHover={{ scale: 1.1 }}
              className="absolute -right-1.5 -top-1.5 h-6 w-6 rounded-full bg-card border shadow-md flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={handleCopy}
            >
              {copied ? (
                <Check className="h-3 w-3 text-green-500" />
              ) : (
                <Copy className="h-3 w-3 text-muted-foreground" />
              )}
            </motion.button>
          )}

          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            <div className="prose-custom text-sm">
              {message.isStreaming && !message.content ? (
                <TypingIndicator />
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              )}
            </div>
          )}
        </div>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-col gap-1.5 w-full"
          >
            <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
              <Sparkles className="h-2.5 w-2.5 text-purple-500" />
              <span className="font-semibold uppercase tracking-wider">Sources</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {message.sources.map((source, idx) => (
                <div
                  key={idx}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] glass border border-border/50 hover:border-primary/50 cursor-help transition-all"
                  title={source.preview}
                >
                  <FileText className="h-2.5 w-2.5 text-blue-500" />
                  <span className="font-medium truncate max-w-[150px]">{source.document_name}</span>
                  {source.page_number && (
                    <span className="text-muted-foreground">
                      p{source.page_number}
                    </span>
                  )}
                  <span className={cn(
                    "ml-0.5 px-1 py-0 rounded-full text-[9px] font-bold",
                    source.similarity_score > 0.7 
                      ? "bg-green-500/20 text-green-500"
                      : source.similarity_score > 0.5
                      ? "bg-yellow-500/20 text-yellow-500"
                      : "bg-orange-500/20 text-orange-500"
                  )}>
                    {Math.round(source.similarity_score * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Timestamp (Compact) */}
        <div className={cn(
          "flex items-center gap-1.5 text-[10px] text-muted-foreground/60",
          isUser ? "flex-row-reverse" : "flex-row"
        )}>
          <span>
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          {!isUser && !message.isStreaming && message.content && (
            <>
              <span>•</span>
              <span className="flex items-center gap-0.5">
                <Zap className="h-2.5 w-2.5 text-yellow-500" />
                AI
              </span>
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 py-0.5">
      <span className="text-xs text-muted-foreground">Thinking</span>
      <div className="flex items-center gap-0.5">
        <span className="typing-dot inline-block w-1.5 h-1.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full" />
        <span className="typing-dot inline-block w-1.5 h-1.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full" />
        <span className="typing-dot inline-block w-1.5 h-1.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full" />
      </div>
    </div>
  );
}