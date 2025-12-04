import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatContainer } from './components/ChatContainer';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ChatContainer />
    </QueryClientProvider>
  );
}

export default App;
