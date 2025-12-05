import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
}

const InfoPopup: React.FC = () => {
  const [showPopup, setShowPopup] = useState(false);

  return (
    <div className="relative inline-block ml-2">
      <button
        onClick={() => setShowPopup(!showPopup)}
        className="inline-flex items-center justify-center w-4 h-4 text-xs text-gray-500 hover:text-gray-700 border border-gray-400 rounded-full"
        title="About confidence scores"
      >
        i
      </button>

      {showPopup && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowPopup(false)}
          />

          {/* Popup */}
          <div className="absolute left-0 top-6 z-50 w-96 bg-white border-2 border-gray-300 rounded-lg shadow-xl p-4">
            <div className="flex justify-between items-start mb-3">
              <h3 className="font-bold text-sm text-gray-900">Understanding Scores</h3>
              <button
                onClick={() => setShowPopup(false)}
                className="text-gray-400 hover:text-gray-600 text-lg leading-none"
              >
                ×
              </button>
            </div>

            <div className="space-y-3 text-xs text-gray-700">
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Confidence Percentage (45% / 75% / 92%)</h4>
                <p>This is <strong>GPT-4's self-assessment</strong> of how well it can answer based on the retrieved sources. GPT-4 reads all source text and decides: "Do these sources fully answer the question?"</p>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Source Match Score (0.0 - 1.0)</h4>
                <p>This is the <strong>retrieval score</strong> showing how similar each chunk is to your query (70% semantic similarity + 30% keyword matching). Scores of 0.3-0.5 indicate relevant, on-topic chunks.</p>
              </div>

              <div className="pt-2 border-t border-gray-200">
                <p className="italic text-gray-600">
                  <strong>Why they're different:</strong> Retrieval scores measure "Did we find relevant chunks?" while confidence measures "Can we fully answer the question with what we found?"
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const ConfidenceBadge: React.FC<{ confidence: 'low' | 'medium' | 'high' }> = ({ confidence }) => {
  const colors = {
    low: 'bg-red-100 text-red-800 border-red-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    high: 'bg-green-100 text-green-800 border-green-200',
  };

  const percentages = {
    low: '45%',
    medium: '75%',
    high: '92%',
  };

  return (
    <span className={`px-2 py-1 text-xs font-semibold rounded-full border ${colors[confidence]}`}>
      {percentages[confidence]} CONFIDENCE
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
                <div className="flex items-center">
                  <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">Confidence:</span>
                  <InfoPopup />
                </div>
                <ConfidenceBadge confidence={message.response.confidence} />
              </div>
            )}

            {/* Answer Content */}
            <div className="px-6 py-5">
              <div className="text-gray-800 leading-relaxed text-base whitespace-pre-wrap">
                {formatAnswerWithSourceBadges(message.content)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
