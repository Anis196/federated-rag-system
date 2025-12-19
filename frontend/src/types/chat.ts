export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: string[];
}

export interface ChatRequest {
  message: string;
  conversationId?: string;
  attachments?: string[];
}

export interface ChatResponse {
  response: string;
  conversationId: string;
  timestamp: string;
}

export interface ConversationHistory {
  conversationId: string;
  messages: Message[];
}
