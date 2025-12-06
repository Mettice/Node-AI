import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Workflow, Menu, X } from 'lucide-react';
import { cn } from '@/utils/cn';

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={cn(
      "fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b",
      isScrolled 
        ? "bg-slate-950/80 backdrop-blur-md border-slate-800" 
        : "bg-transparent border-transparent"
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Workflow className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-white tracking-tight">
              NodeAI
            </span>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center space-x-8">
            <a href="#features" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Features</a>
            <a href="#industries" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Industries</a>
            <a href="#observability" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Observability</a>
            <a href="#security" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Security</a>
            <a href="#pricing" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Pricing</a>
          </div>

          {/* CTA Buttons */}
          <div className="hidden md:flex items-center gap-4">
            <Link 
              to="/login" 
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
            >
              Log in
            </Link>
            <Link 
              to="/register" 
              className="bg-white text-slate-950 px-4 py-2 rounded-md text-sm font-semibold hover:bg-slate-200 transition-all"
            >
              Start Building
            </Link>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-slate-400 hover:text-white p-2"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden top-16">
          <div className="absolute inset-0 bg-slate-950 border-t border-slate-800 p-4">
            <div className="flex flex-col space-y-4">
              <a href="#features" className="text-slate-400 hover:text-white py-2" onClick={() => setMobileMenuOpen(false)}>Features</a>
              <a href="#industries" className="text-slate-400 hover:text-white py-2" onClick={() => setMobileMenuOpen(false)}>Industries</a>
              <a href="#observability" className="text-slate-400 hover:text-white py-2" onClick={() => setMobileMenuOpen(false)}>Observability</a>
              <a href="#security" className="text-slate-400 hover:text-white py-2" onClick={() => setMobileMenuOpen(false)}>Security</a>
              <a href="#pricing" className="text-slate-400 hover:text-white py-2" onClick={() => setMobileMenuOpen(false)}>Pricing</a>
              <div className="h-px bg-slate-800 my-2" />
              <Link to="/login" className="text-slate-300 hover:text-white py-2" onClick={() => setMobileMenuOpen(false)}>Log in</Link>
              <Link to="/register" className="bg-white text-slate-950 py-3 rounded-md text-center font-semibold" onClick={() => setMobileMenuOpen(false)}>Start Building</Link>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
