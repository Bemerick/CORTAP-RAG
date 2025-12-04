import React, { useState } from 'react';
import type { SourceCitation as SourceCitationType } from '../types';

interface SourceCitationProps {
  sources: SourceCitationType[];
}

export const SourceCitation: React.FC<SourceCitationProps> = ({ sources }) => {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 border-t pt-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center text-sm font-medium text-blue-600 hover:text-blue-800"
      >
        <span>{expanded ? '▼' : '▶'}</span>
        <span className="ml-2">View Sources ({sources.length})</span>
      </button>

      {expanded && (
        <div className="mt-3 space-y-3">
          {sources.map((source, idx) => (
            <div key={idx} className="bg-white border rounded p-3 text-sm">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span className="font-semibold text-gray-700">
                    {source.category.replace(/_/g, ' ')}
                  </span>
                  <span className="ml-2 text-gray-500 text-xs">
                    ({source.chunk_id})
                  </span>
                </div>
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  Score: {source.score.toFixed(3)}
                </span>
              </div>
              <p className="text-gray-600 text-xs leading-relaxed">
                {source.excerpt}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
