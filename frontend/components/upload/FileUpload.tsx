"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileUp, Loader2, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import toast from "react-hot-toast";

interface FileUploadProps {
  onUploadComplete?: () => void;
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [uploading, setUploading] = useState<Map<string, number>>(new Map());

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      for (const file of acceptedFiles) {
        const fileId = `${file.name}-${Date.now()}`;
        setUploading((prev) => new Map(prev).set(fileId, 0));

        try {
          const response = await api.uploadFile(file, (progress) => {
            setUploading((prev) => new Map(prev).set(fileId, progress));
          });

          if (response.status === "duplicate") {
            toast(`${file.name} already exists`, { icon: "ℹ️" });
          } else {
            toast.success(`${file.name} processed!`);
          }

          if (onUploadComplete) onUploadComplete();
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : "Upload failed";
          toast.error(`${file.name}: ${message}`);
        } finally {
          setUploading((prev) => {
            const newMap = new Map(prev);
            newMap.delete(fileId);
            return newMap;
          });
        }
      }
    },
    [onUploadComplete]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "text/csv": [".csv"],
      "text/plain": [".txt"],
      "text/html": [".html"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
    },
    maxSize: 50 * 1024 * 1024,
  });

  return (
    <div className="space-y-3">
      <motion.div
        {...getRootProps()}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        animate={{
          borderColor: isDragActive 
            ? "rgb(168, 85, 247)" 
            : "rgba(168, 85, 247, 0.3)",
        }}
        className={cn(
          "relative border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer overflow-hidden",
          "transition-all duration-300",
          isDragActive
            ? "border-purple-500 bg-purple-500/5"
            : "border-border hover:border-purple-500/50 hover:bg-accent/50"
        )}
      >
        <input {...getInputProps()} />
        
        {/* Animated background */}
        <AnimatePresence>
          {isDragActive && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-blue-500/10"
            />
          )}
        </AnimatePresence>

        <motion.div
          animate={{ 
            y: isDragActive ? -5 : 0,
            scale: isDragActive ? 1.1 : 1,
          }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
          className="relative"
        >
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-500 to-blue-500 shadow-lg mb-3">
            {isDragActive ? (
              <FileUp className="h-6 w-6 text-white" />
            ) : (
              <Upload className="h-6 w-6 text-white" />
            )}
          </div>

          {isDragActive ? (
            <p className="text-sm font-semibold text-purple-500">
              Drop your files here!
            </p>
          ) : (
            <>
              <p className="text-sm font-semibold mb-1">
                Drop files or click to upload
              </p>
              <p className="text-xs text-muted-foreground">
                PDF, DOCX, XLSX, CSV, TXT, Images
              </p>
            </>
          )}
        </motion.div>
      </motion.div>

      {/* Upload Progress */}
      <AnimatePresence>
        {uploading.size > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            {Array.from(uploading.entries()).map(([fileId, progress]) => (
              <motion.div
                key={fileId}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="glass p-3 rounded-xl border border-border/50"
              >
                <div className="flex items-center gap-2 mb-2">
                  {progress === 100 ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <Loader2 className="h-4 w-4 animate-spin text-purple-500" />
                  )}
                  <span className="text-xs font-medium truncate flex-1">
                    {fileId.split("-").slice(0, -1).join("-")}
                  </span>
                  <span className="text-xs font-semibold text-primary">
                    {progress}%
                  </span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
