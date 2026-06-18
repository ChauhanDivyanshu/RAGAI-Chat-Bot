export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  sources?: Source[];
  isStreaming?: boolean;
  error?: boolean;
}

export interface Source {
  document_name: string;
  page_number?: number | null;
  chunk_index?: number | null;
  similarity_score: number;
  preview: string;
}

export interface QueryStats {
  chunks_found: number;
  model: string;
  tokens_used: number;
  retrieval_time_ms: number;
  llm_time_ms: number;
  total_time_ms: number;
  cached: boolean;
  detected_language?: string;
}

export interface QueryResponse {
  success: boolean;
  question: string;
  answer: string;
  sources: Source[];
  stats: QueryStats;
  conversation_id?: string;
}

export interface Document {
  id: string;
  name: string;
  file_type?: string;
  size_bytes: number;
  size_readable: string;
  pages?: number;
  chunks: number;
  status: string;
  language?: string;
  uploaded_at?: string;
  processed_at?: string;
}

export interface UploadResponse {
  success: boolean;
  status: string;
  document_id: string;
  filename: string;
  file_size: number;
  file_size_readable: string;
  pages?: number;
  characters?: number;
  chunks_created: number;
  chunks_saved: number;
  processing_time_ms?: number;
  message: string;
}

export interface DocumentListResponse {
  total: number;
  documents: Document[];
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  timestamp: string;
}
