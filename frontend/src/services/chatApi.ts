import { ChatRequest, ChatResponse } from '@/types/chat';

// Configure your Spring Boot backend URL here
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';

export const chatApi = {
  /**
   * Send a message to the RAG chatbot backend
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/rag/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get conversation history by ID
   */
  async getConversationHistory(conversationId: string) {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch conversation: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Upload file attachments
   */
  async uploadAttachment(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.fileUrl;
  },
};
