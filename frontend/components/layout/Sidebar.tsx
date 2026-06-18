"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  FileText, Trash2, RefreshCw, Menu, X, 
  FileSpreadsheet, Image as ImageIcon, FileCode,
  Sparkles, Activity
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { FileUpload } from "@/components/upload/FileUpload";
import { ThemeToggle } from "@/components/theme-toggle";
import { api } from "@/lib/api";
import type { Document } from "@/types";
import toast from "react-hot-toast";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await api.getDocuments();
      setDocuments(response.documents);
    } catch (error) {
      toast.error("Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"?`)) return;
    try {
      await api.deleteDocument(id);
      toast.success(`Deleted: ${name}`);
      loadDocuments();
    } catch (error) {
      toast.error("Failed to delete document");
    }
  };

  const getFileIcon = (type?: string) => {
    if (!type) return FileText;
    const t = type.toLowerCase();
    if (t.includes("pdf")) return FileText;
    if (t.includes("xls") || t.includes("csv")) return FileSpreadsheet;
    if (t.includes("jpg") || t.includes("png") || t.includes("image")) return ImageIcon;
    if (t.includes("html") || t.includes("doc")) return FileCode;
    return FileText;
  };

  const getFileColor = (type?: string) => {
    if (!type) return "from-gray-500 to-gray-600";
    const t = type.toLowerCase();
    if (t.includes("pdf")) return "from-red-500 to-rose-600";
    if (t.includes("xls")) return "from-green-500 to-emerald-600";
    if (t.includes("csv")) return "from-emerald-500 to-teal-600";
    if (t.includes("doc")) return "from-blue-500 to-indigo-600";
    if (t.includes("html")) return "from-orange-500 to-red-600";
    if (t.includes("jpg") || t.includes("png")) return "from-purple-500 to-pink-600";
    if (t.includes("txt")) return "from-gray-500 to-slate-600";
    return "from-cyan-500 to-blue-600";
  };

  const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunks || 0), 0);

  return (
    <>
      <Button
        variant="outline"
        size="icon"
        className="fixed top-4 left-4 z-50 md:hidden glass"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
      </Button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40 md:hidden"
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>

      <motion.aside
        initial={false}
        animate={{ x: isOpen ? 0 : 0 }}
        className={cn(
          "fixed md:relative z-40 h-full w-75 md:w-75 lg:w-75a",
          "flex flex-col border-r border-border/40 glass-strong",
          "transition-transform duration-300",
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        {/* ───── HEADER ───── */}
        <div className="p-4 border-b border-border/40 flex-shrink-0">
          <div className="flex items-center justify-between">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/30 to-blue-500/30 blur-xl" />
                <svg viewBox="0 0 50 50" className="w-9 h-9 relative" fill="none">
                  <path
                    d="M25 8 Q17 14, 14 22 Q12 28, 17 32"
                    stroke="url(#sbLaurel)"
                    strokeWidth="2"
                    strokeLinecap="round"
                    fill="none"
                  />
                  <path
                    d="M25 8 Q33 14, 36 22 Q38 28, 33 32"
                    stroke="url(#sbLaurel)"
                    strokeWidth="2"
                    strokeLinecap="round"
                    fill="none"
                  />
                  <ellipse cx="17" cy="16" rx="2" ry="4" fill="url(#sbLeaf)" transform="rotate(-30 17 16)" />
                  <ellipse cx="14" cy="22" rx="2" ry="4" fill="url(#sbLeaf)" transform="rotate(-45 14 22)" />
                  <ellipse cx="33" cy="16" rx="2" ry="4" fill="url(#sbLeaf)" transform="rotate(30 33 16)" />
                  <ellipse cx="36" cy="22" rx="2" ry="4" fill="url(#sbLeaf)" transform="rotate(45 36 22)" />
                  <line x1="25" y1="32" x2="25" y2="44" stroke="url(#sbLaurel)" strokeWidth="2" strokeLinecap="round" />
                  <circle cx="25" cy="8" r="2" fill="url(#sbLeaf)" />
                  
                  <defs>
                    <linearGradient id="sbLaurel" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#a855f7" />
                      <stop offset="100%" stopColor="#3b82f6" />
                    </linearGradient>
                    <linearGradient id="sbLeaf" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#c084fc" />
                      <stop offset="100%" stopColor="#60a5fa" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <div>
                <h2 className="font-serif text-lg font-semibold tracking-tight leading-tight">
                  RAG Assistant
                </h2>
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <p className="text-[10px] text-emerald-400 tracking-wide uppercase font-semibold">
                    Online
                  </p>
                </div>
              </div>
            </motion.div>
            <ThemeToggle />
          </div>
        </div>

        {/* ───── COMPACT STATS ───── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 gap-2 p-4 flex-shrink-0"
        >
          <div className="glass rounded-lg p-2.5 border border-border/30">
            <div className="flex items-center gap-1.5">
              <FileText className="w-3 h-3 text-blue-400" />
              <span className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold">
                Docs
              </span>
            </div>
            <div className="font-serif text-xl font-semibold mt-0.5 gradient-text leading-none">
              {documents.length}
            </div>
          </div>
          <div className="glass rounded-lg p-2.5 border border-border/30">
            <div className="flex items-center gap-1.5">
              <Activity className="w-3 h-3 text-purple-400" />
              <span className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold">
                Chunks
              </span>
            </div>
            <div className="font-serif text-xl font-semibold mt-0.5 gradient-text leading-none">
              {totalChunks}
            </div>
          </div>
        </motion.div>

        {/* ───── UPLOAD ───── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="px-4 pb-3 flex-shrink-0"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-purple-400" />
              <h3 className="text-[10px] font-bold uppercase tracking-widest text-foreground/80">
                Upload
              </h3>
            </div>
            <span className="text-[9px] text-muted-foreground/70 font-medium">
              Max 50MB
            </span>
          </div>
          <FileUpload onUploadComplete={loadDocuments} />
        </motion.div>

        {/* ───── LIBRARY (Scrollable) ───── */}
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="px-4 py-2.5 flex items-center justify-between border-y border-border/40 flex-shrink-0">
            <div className="flex items-center gap-1.5">
              <FileText className="w-3 h-3 text-blue-400" />
              <h3 className="text-[10px] font-bold uppercase tracking-widest text-foreground/80">
                Library
              </h3>
              <motion.span
                key={documents.length}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="px-1.5 py-0.5 text-[9px] font-bold bg-primary/10 text-primary rounded-full"
              >
                {documents.length}
              </motion.span>
            </div>
            <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={loadDocuments}
                disabled={loading}
              >
                <RefreshCw
                  className={cn(
                    "h-3 w-3 transition-transform text-muted-foreground",
                    loading && "animate-spin"
                  )}
                />
              </Button>
            </motion.div>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-2 min-h-0">
            <AnimatePresence mode="popLayout">
              {documents.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-12"
                >
                  <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br from-purple-500/10 to-blue-500/10 flex items-center justify-center border border-border/30">
                    <FileText className="h-5 w-5 text-muted-foreground/50" />
                  </div>
                  <p className="text-xs font-medium text-foreground/70 mb-1">
                    Library is empty
                  </p>
                  <p className="text-[10px] text-muted-foreground/60">
                    Upload your first document
                  </p>
                </motion.div>
              ) : (
                <div className="space-y-2">
                  {documents.map((doc, idx) => {
                    const Icon = getFileIcon(doc.file_type);
                    const colorClass = getFileColor(doc.file_type);

                    return (
                      <motion.div
                        key={doc.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ delay: idx * 0.03 }}
                        whileHover={{ scale: 1.01, x: 2 }}
                        className="group glass rounded-lg p-2.5 hover:border-primary/30 border border-border/30 transition-all cursor-pointer"
                      >
                        <div className="flex items-start gap-2.5">
                          <div className="relative shrink-0">
                            <div className={cn(
                              "absolute inset-0 blur-md opacity-50 rounded-lg",
                              "bg-gradient-to-br",
                              colorClass
                            )} />
                            <div
                              className={cn(
                                "h-8 w-8 rounded-lg flex items-center justify-center shadow-md relative",
                                "bg-gradient-to-br",
                                colorClass
                              )}
                            >
                              <Icon className="h-3.5 w-3.5 text-white" />
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium truncate">
                              {doc.name}
                            </p>
                            <div className="flex items-center gap-1.5 mt-0.5 text-[10px] text-muted-foreground">
                              <span>{doc.size_readable}</span>
                              <span>•</span>
                              <span>{doc.chunks} chunks</span>
                            </div>
                            <div className="flex items-center gap-1 mt-1.5">
                              <span
                                className={cn(
                                  "px-1.5 py-0.5 text-[9px] font-semibold rounded-full",
                                  doc.status === "completed"
                                    ? "bg-emerald-500/10 text-emerald-400"
                                    : "bg-amber-500/10 text-amber-400"
                                )}
                              >
                                {doc.status === "completed" ? "✓" : "⏳"} {doc.status}
                              </span>
                              {doc.file_type && (
                                <span className="px-1.5 py-0.5 text-[9px] font-semibold bg-muted/60 text-muted-foreground rounded-full uppercase tracking-wider">
                                  {doc.file_type}
                                </span>
                              )}
                            </div>
                          </div>
                          <motion.button
                            whileHover={{ scale: 1.2 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => handleDelete(doc.id, doc.name)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-lg hover:bg-destructive/10"
                          >
                            <Trash2 className="h-3 w-3 text-destructive" />
                          </motion.button>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* ───── COMPACT FOOTER (No duplicates) ───── */}
        <div className="p-3 border-t border-border/40 flex-shrink-0">
          <div className="flex items-center justify-center gap-1.5 flex-wrap">
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[9px] font-bold text-emerald-400">
              BGE-M3
            </span>
            <span className="text-muted-foreground text-[10px]">×</span>
            <span className="px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-[9px] font-bold text-purple-400">
              Qwen 2.5
            </span>
            <span className="text-muted-foreground text-[10px]">×</span>
            <span className="px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-[9px] font-bold text-blue-400">
              pgvector
            </span>
          </div>
        </div>
      </motion.aside>
    </>
  );
}