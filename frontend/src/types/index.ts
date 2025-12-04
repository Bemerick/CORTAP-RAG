export interface SourceCitation {
  chunk_id: string;
  category: string;
  excerpt: string;
  score: number;
  file_path: string;
  page_range?: string;
}

export interface QueryResponse {
  answer: string;
  confidence: 'low' | 'medium' | 'high';
  sources: SourceCitation[];
  ranked_chunks: SourceCitation[];
}

export interface ConversationMessage {
  role: string;
  content: string;
}

export interface QueryRequest {
  question: string;
  recipient_type?: string;
  conversation_history?: ConversationMessage[];
}

export interface CommonQuestion {
  question: string;
  category: string;
}

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  response?: QueryResponse;
  timestamp: Date;
}
