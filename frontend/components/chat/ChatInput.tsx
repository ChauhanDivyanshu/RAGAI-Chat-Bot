"use client";

import { useState, KeyboardEvent, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <motion.div
      initial={{ y: 50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="border-t glass-strong p-4 md:p-6"
    >
      <div className="max-w-4xl mx-auto">
        <motion.div
          animate={{
            scale: isFocused ? 1.01 : 1,
            boxShadow: isFocused
              ? "0 20px 40px -10px rgba(102, 126, 234, 0.3)"
              : "0 4px 12px -2px rgba(0, 0, 0, 0.1)",
          }}
          transition={{ duration: 0.2 }}
          className={cn(
            "relative flex gap-2 items-end rounded-2xl border bg-card p-2 transition-all",
            isFocused ? "border-primary/50" : "border-border"
          )}
        >
          {/* Sparkle icon */}
          <div className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
            <Sparkles className={cn(
              "h-4 w-4 transition-colors",
              isFocused ? "text-primary" : "text-muted-foreground"
            )} />
          </div>

          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Ask anything... (English, Hindi, Hinglish)"
            disabled={disabled}
            rows={1}
            className={cn(
              "resize-none min-h-[44px] max-h-[200px] border-0 bg-transparent",
              "focus-visible:ring-0 focus-visible:ring-offset-0",
              "pl-10 pr-2 text-sm"
            )}
          />

          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Button
              onClick={handleSend}
              disabled={!input.trim() || disabled}
              size="icon"
              className={cn(
                "h-11 w-11 shrink-0 rounded-xl shadow-md",
                "bg-gradient-to-br from-purple-500 to-blue-600",
                "hover:from-purple-600 hover:to-blue-700",
                "disabled:from-muted disabled:to-muted",
                "transition-all"
              )}
            >
              <AnimatePresence mode="wait">
                {disabled ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0, rotate: -180 }}
                    animate={{ opacity: 1, rotate: 0 }}
                    exit={{ opacity: 0, rotate: 180 }}
                  >
                    <Loader2 className="h-4 w-4 animate-spin text-white" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="send"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                  >
                    <Send className="h-4 w-4 text-white" />
                  </motion.div>
                )}
              </AnimatePresence>
            </Button>
          </motion.div>
        </motion.div>

        <div className="flex items-center justify-between mt-3 px-2">
          <p className="text-xs text-muted-foreground">
            Press <kbd className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">Enter</kbd> to send
          </p>
          <p className="text-xs text-muted-foreground">
            🌐 English • हिंदी • Hinglish
          </p>
        </div>
      </div>
    </motion.div>
  );
}
