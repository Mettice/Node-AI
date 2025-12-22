/**
 * Register Page
 */

import { Link } from 'react-router-dom';
import { RegisterForm } from '@/components/Auth/RegisterForm';
import { AnimatedBackground } from '@/components/landing/AnimatedBackground';

export function RegisterPage() {
  return (
    <div className="min-h-screen bg-[#030712] flex items-center justify-center p-4 sm:p-6 relative">
      <AnimatedBackground />
      <div className="w-full max-w-sm sm:max-w-md relative z-10">
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-3xl sm:text-4xl font-black text-white mb-2 bg-gradient-to-r from-amber-400 to-pink-400 bg-clip-text text-transparent">NodeAI</h1>
          <p className="text-slate-400 text-sm sm:text-base">Create your account</p>
        </div>
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl">
          <RegisterForm />
        </div>
        <div className="mt-4 sm:mt-6 text-center text-xs sm:text-sm text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-amber-400 hover:text-amber-300 font-medium transition-colors">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

