import ReactMarkdown from 'react-markdown';
import type { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
}

const ConfidenceBadge: React.FC<{ confidence: 'low' | 'medium' | 'high' }> = ({ confidence }) => {
  const colors = {
    low: 'bg-red-100 text-red-800 border-red-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    high: 'bg-green-100 text-green-800 border-green-200',
  };

  const percentages = {
    low: '< 60%',
    medium: '60-85%',
    high: '> 85%',
  };

  return (
    <span className={`px-2 py-1 text-xs font-semibold rounded-full border ${colors[confidence]}`}>
      {confidence.toUpperCase()} ({percentages[confidence]})
    </span>
  );
};

const SourceBadge: React.FC<{ number: number }> = ({ number }) => {
  return (
    <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-orange-500 rounded-full ml-1">
      {number}
    </span>
  );
};

const formatAnswerWithSourceBadges = (text: string) => {
  // Replace [Source N] with styled badges
  return text.split(/(\[Source \d+\])/g).map((part, index) => {
    const match = part.match(/\[Source (\d+)\]/);
    if (match) {
      return <SourceBadge key={index} number={parseInt(match[1])} />;
    }
    return <span key={index}>{part}</span>;
  });
};

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.type === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`max-w-3xl w-full ${isUser ? 'bg-blue-600 text-white rounded-lg px-4 py-3 shadow' : ''}`}>
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            {/* Confidence Badge Header */}
            {message.response && (
              <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-4 py-3 border-b border-gray-200 flex items-center gap-2">
                <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">Confidence:</span>
                <ConfidenceBadge confidence={message.response.confidence} />
              </div>
            )}

            {/* Answer Content */}
            <div className="px-6 py-5">
              <div className="text-gray-800 leading-relaxed text-base">
                {formatAnswerWithSourceBadges(message.content)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
