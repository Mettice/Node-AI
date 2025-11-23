/**
 * Register Page
 */

import { Link } from 'react-router-dom';
import { RegisterForm } from '@/components/Auth/RegisterForm';

export function RegisterPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/20 to-slate-950 flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-sm sm:max-w-md">
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2 bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">NodAI</h1>
          <p className="text-slate-400 text-sm sm:text-base">Create your account</p>
        </div>
        <div className="bg-slate-800/50 backdrop-blur-sm border border-white/10 rounded-xl p-6 sm:p-8">
          <RegisterForm />
        </div>
        <div className="mt-4 sm:mt-6 text-center text-xs sm:text-sm text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-purple-400 hover:text-purple-300 font-medium">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

