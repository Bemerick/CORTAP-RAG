import axios from 'axios';
import type { QueryRequest, QueryResponse, CommonQuestion } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const queryAPI = {
  async askQuestion(request: QueryRequest): Promise<QueryResponse> {
    const response = await api.post<QueryResponse>('/api/v1/query', request);
    return response.data;
  },

  async getCommonQuestions(): Promise<CommonQuestion[]> {
    const response = await api.get<CommonQuestion[]>('/api/v1/common-questions');
    return response.data;
  },

  async healthCheck(): Promise<{ status: string; database_ready: boolean }> {
    const response = await api.get('/api/v1/health');
    return response.data;
  },
};

export default api;
