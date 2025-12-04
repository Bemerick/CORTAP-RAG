import { useQuery } from '@tanstack/react-query';
import { queryAPI } from '../services/api';
import type { CommonQuestion } from '../types';

interface SuggestedQuestionsProps {
  onQuestionClick: (question: string) => void;
}

export const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({ onQuestionClick }) => {
  const { data: questions, isLoading } = useQuery({
    queryKey: ['common-questions'],
    queryFn: queryAPI.getCommonQuestions,
  });

  if (isLoading) {
    return (
      <div className="text-center text-gray-500 text-sm">
        Loading suggested questions...
      </div>
    );
  }

  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Common Questions</h3>
      <div className="flex flex-wrap gap-2">
        {questions.map((q: CommonQuestion, idx: number) => (
          <button
            key={idx}
            onClick={() => onQuestionClick(q.question)}
            className="px-3 py-2 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg border border-blue-200 transition"
          >
            {q.question}
          </button>
        ))}
      </div>
    </div>
  );
};
