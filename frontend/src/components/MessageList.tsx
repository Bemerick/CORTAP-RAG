import React, { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { SourceCitation } from './SourceCitation';
import type { Message } from '../types';

interface MessageListProps {
  messages: Message[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="text-center text-gray-500 mt-20">
          <h2 className="text-2xl font-bold text-gray-700 mb-2">
            FTA Compliance Assistant
          </h2>
          <p>Ask a question about FTA compliance requirements</p>
        </div>
      ) : (
        messages.map((message) => (
          <div key={message.id}>
            <MessageBubble message={message} />
            {message.type === 'assistant' && message.response && (
              <div className="ml-4 max-w-3xl">
                <SourceCitation sources={message.response.ranked_chunks} />
              </div>
            )}
          </div>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
};
