import { useState, useCallback } from 'react';
import { Message, ChatRequest } from '@/types/chat';
import { chatApi } from '@/services/chatApi';
import { useToast } from '@/hooks/use-toast';

export function useChatMessages() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const { toast } = useToast();

  const sendMessage = useCallback(async (content: string, attachments?: string[]) => {
    // Add user message immediately
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
      attachments,
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const request: ChatRequest = {
        message: content,
        conversationId,
        attachments,
      };

      const response = await chatApi.sendMessage(request);

      console.log('[useChatMessages] API Response:', response);

      // Add assistant response
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.timestamp),
      };

      console.log('[useChatMessages] Creating assistant message:', assistantMessage);

      setMessages(prev => {
        const updated = [...prev, assistantMessage];
        console.log('[useChatMessages] Messages updated to:', updated);
        return updated;
      });
      setConversationId(response.conversationId);

      console.log('[useChatMessages] Message sent successfully');
    } catch (error) {
      console.error('Error sending message:', error);
      toast({
        title: 'Error',
        description: 'Failed to send message. Please try again.',
        variant: 'destructive',
      });

      // Remove the user message on error
      setMessages(prev => prev.filter(m => m.id !== userMessage.id));
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, toast]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(undefined);
  }, []);

  return {
    messages,
    isLoading,
    conversationId,
    sendMessage,
    clearMessages,
  };
}
