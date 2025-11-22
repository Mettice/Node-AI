/**
 * Login Page
 */

import { Link } from 'react-router-dom';
import { LoginForm } from '@/components/Auth/LoginForm';

export function LoginPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">NodAI</h1>
          <p className="text-slate-400">Sign in to your account</p>
        </div>
        <LoginForm />
        <div className="mt-6 text-center text-sm text-slate-400">
          Don't have an account?{' '}
          <Link to="/register" className="text-purple-400 hover:text-purple-300 font-medium">
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}

