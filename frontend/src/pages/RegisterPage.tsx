/**
 * Register Page
 */

import { Link } from 'react-router-dom';
import { RegisterForm } from '@/components/Auth/RegisterForm';

export function RegisterPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">NodAI</h1>
          <p className="text-slate-400">Create your account</p>
        </div>
        <RegisterForm />
        <div className="mt-6 text-center text-sm text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-purple-400 hover:text-purple-300 font-medium">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

