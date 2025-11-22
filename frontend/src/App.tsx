/**
 * Main App component
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { checkHealth } from '@/services/health';
import { Spinner } from '@/components/common/Spinner';
import { ProtectedRoute } from '@/components/Auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { HomePage } from '@/pages/HomePage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const { loading: authLoading } = useAuth();

  useEffect(() => {
    // Check API health on mount
    checkHealth()
      .then(() => {
        setIsConnected(true);
        setIsChecking(false);
      })
      .catch((error) => {
        console.error('Failed to connect to API:', error);
        setIsConnected(false);
        setIsChecking(false);
      });
  }, []);

  if (isChecking || authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Spinner size="lg" className="mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center p-8 bg-white rounded-lg shadow-md max-w-md">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">NodeAI</h1>
          <p className="text-red-600 mb-4">
            Failed to connect to backend API
          </p>
          <p className="text-gray-600 text-sm mb-4">
            Make sure the backend server is running on{' '}
            <code className="bg-gray-100 px-2 py-1 rounded">
              http://localhost:8000
            </code>
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Protected route - main application */}
        <Route
          path="/*"
          element={
            <ProtectedRoute requireAuth={false}>
              <HomePage />
            </ProtectedRoute>
          }
        />
      </Routes>

      {/* Toast notifications */}
      <Toaster position="top-right" />
    </QueryClientProvider>
  );
}

export default App;
