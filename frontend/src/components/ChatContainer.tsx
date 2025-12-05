import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';
import { SuggestedQuestions } from './SuggestedQuestions';
import { ComplianceAreaSelector } from './ComplianceAreaSelector';
import { queryAPI } from '../services/api';
import type { Message } from '../types';

export const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);

  const mutation = useMutation({
    mutationFn: queryAPI.askQuestion,
    onSuccess: (data) => {
      // Use the answer directly from backend (backend handles all formatting)
      const assistantMessage: Message = {
        id: Date.now().toString() + '-assistant',
        type: 'assistant',
        content: data.answer,
        response: data,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    },
    onError: (error) => {
      const errorMessage: Message = {
        id: Date.now().toString() + '-error',
        type: 'assistant',
        content: `Sorry, I encountered an error: ${error.message}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    },
  });

  const handleSendMessage = (question: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Build conversation history from previous messages
    const conversation_history = messages.map((m: Message) => ({
      role: m.type === 'user' ? 'user' : 'assistant',
      content: m.content
    }));

    mutation.mutate({ question, conversation_history });
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 shadow-md">
        <h1 className="text-xl font-bold">CORTAP-RAG: FTA Compliance Assistant</h1>
        <p className="text-sm text-blue-100">Ask questions about FTA compliance requirements</p>
      </div>

      {/* Compliance Area Selector */}
      <ComplianceAreaSelector onSubmit={handleSendMessage} />

      {/* Suggested Questions */}
      {messages.length === 0 && (
        <div className="p-4 bg-white border-b">
          <SuggestedQuestions onQuestionClick={handleSendMessage} />
        </div>
      )}

      {/* Messages */}
      <MessageList messages={messages} />

      {/* Input */}
      <InputBar onSend={handleSendMessage} disabled={mutation.isPending} />

      {/* Loading indicator */}
      {mutation.isPending && (
        <div className="fixed bottom-20 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg">
          Processing your question...
        </div>
      )}
    </div>
  );
};
