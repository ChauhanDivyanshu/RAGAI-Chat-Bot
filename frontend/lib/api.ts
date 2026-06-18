import axios, { AxiosProgressEvent } from "axios";
import type { Document, QueryResponse } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// ⚡ Increase timeout to 5 minutes for slow LLM
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 300000, // 5 minutes (was 2 min)
  headers: {
    "Content-Type": "application/json",
  },
});

export const api = {
  // ─── GET DOCUMENTS ───
  async getDocuments() {
    const response = await apiClient.get("/documents");
    return response.data;
  },

  // ─── DELETE DOCUMENT ───
  async deleteDocument(id: string) {
    const response = await apiClient.delete(`/documents/${id}`);
    return response.data;
  },

  // ─── UPLOAD FILE ───
  async uploadFile(
    file: File,
    onProgress?: (progress: number) => void
  ) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiClient.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 600000, // ⚡ 10 minutes for upload
      onUploadProgress: (event: AxiosProgressEvent) => {
        if (event.total && onProgress) {
          const progress = Math.round((event.loaded * 100) / event.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  },

  // ─── QUERY (with retry) ───
  async query(
    question: string,
    options?: { top_k?: number; document_id?: string }
  ): Promise<QueryResponse> {
    try {
      const response = await apiClient.post("/query", {
        question,
        top_k: options?.top_k || 3,
        document_id: options?.document_id,
      }, {
        timeout: 300000, // ⚡ 5 minutes for query
      });

      return response.data;
    } catch (error: any) {
      // Better error messages
      if (error.code === 'ECONNABORTED') {
        throw new Error("Request timeout - AI is taking too long. Try a simpler question.");
      }
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || "Failed to get response");
    }
  },
};