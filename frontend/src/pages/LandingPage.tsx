/**
 * NodAI Landing Page
 * Modern, developer-focused landing page for the AI workflow platform
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  ArrowRight, Play, Zap, DollarSign, Shield, Code, 
  BarChart3, Users, CheckCircle, Star, Github, 
  Cpu, Database, Brain, Target, TrendingDown,
  Monitor, Lock, Cloud, Workflow, Eye, Key,
  Rocket, BookOpen, TrendingUp, Activity, 
  FileText, Search, Layers, Settings
} from 'lucide-react';
import { cn } from '@/utils/cn';

export function LandingPage() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/20 to-slate-950 text-white overflow-hidden">
      {/* Navigation */}
      <nav className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        isScrolled ? "bg-slate-950/80 backdrop-blur-xl border-b border-purple-500/20" : "bg-transparent"
      )}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg flex items-center justify-center">
                <Workflow className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                NodAI
              </span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-slate-300 hover:text-white transition-colors">Features</a>
              <a href="#observability" className="text-slate-300 hover:text-white transition-colors">Observability</a>
              <a href="#industries" className="text-slate-300 hover:text-white transition-colors">Industries</a>
              <a href="#pricing" className="text-slate-300 hover:text-white transition-colors">Pricing</a>
              <Link 
                to="/login" 
                className="text-slate-300 hover:text-white transition-colors"
              >
                Login
              </Link>
              <Link 
                to="/register" 
                className="bg-gradient-to-r from-purple-500 to-cyan-500 px-4 py-2 rounded-lg text-white font-semibold hover:shadow-lg hover:shadow-purple-500/25 transition-all"
              >
                Start Free
              </Link>
            </div>
            
            {/* Mobile menu button */}
            <div className="md:hidden">
              <button 
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="text-slate-400 hover:text-white p-2"
              >
                {mobileMenuOpen ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation Menu */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)} />
          <div className="fixed top-0 right-0 h-full w-64 bg-slate-900/95 backdrop-blur-lg border-l border-purple-500/20">
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <span className="text-xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                NodAI
              </span>
              <button 
                onClick={() => setMobileMenuOpen(false)}
                className="text-slate-400 hover:text-white p-2"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-4 space-y-4">
              <a href="#features" className="block text-slate-300 hover:text-white py-2 transition-colors">Features</a>
              <a href="#observability" className="block text-slate-300 hover:text-white py-2 transition-colors">Observability</a>
              <a href="#industries" className="block text-slate-300 hover:text-white py-2 transition-colors">Industries</a>
              <a href="#pricing" className="block text-slate-300 hover:text-white py-2 transition-colors">Pricing</a>
              <div className="border-t border-white/10 pt-4 mt-4 space-y-3">
                <Link 
                  to="/login" 
                  className="block text-slate-300 hover:text-white py-2 transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Login
                </Link>
                <Link 
                  to="/register" 
                  className="block bg-gradient-to-r from-purple-500 to-cyan-500 px-4 py-3 rounded-lg text-white font-semibold text-center transition-all"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Start Free
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="pt-24 md:pt-32 pb-12 md:pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12 md:mb-16">
            <div className="inline-flex items-center gap-2 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 border border-purple-500/20 rounded-full px-3 md:px-4 py-2 mb-6 md:mb-8 backdrop-blur-sm">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-xs md:text-sm text-purple-300">Trusted by 10,000+ AI teams worldwide</span>
            </div>
            
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-7xl font-bold mb-4 md:mb-6 leading-tight px-2">
              <span className="block">Production AI Platform</span>
              <span className="block bg-gradient-to-r from-purple-400 via-cyan-400 to-green-400 bg-clip-text text-transparent">
                From Development to Production
              </span>
            </h1>
            
            <p className="text-base sm:text-lg md:text-xl text-slate-400 mb-6 md:mb-8 max-w-4xl mx-auto leading-relaxed px-2">
              Build, deploy, and monitor enterprise-grade AI systems. Multi-agent orchestration, production observability, 
              and enterprise security—all in one platform. Deploy in minutes, monitor forever.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-3 md:gap-4 justify-center mb-8 md:mb-12 px-4">
              <Link 
                to="/register"
                className="bg-gradient-to-r from-purple-500 to-cyan-500 px-6 md:px-8 py-3 md:py-4 rounded-xl text-white font-semibold hover:shadow-lg hover:shadow-purple-500/25 transition-all flex items-center justify-center gap-2 group hover:scale-105 text-sm md:text-base"
              >
                <span className="hidden sm:inline">Build Your First Agent</span>
                <span className="sm:hidden">Get Started</span>
                <ArrowRight className="w-4 md:w-5 h-4 md:h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <button className="border border-slate-600 px-6 md:px-8 py-3 md:py-4 rounded-xl text-white font-semibold hover:bg-slate-800 transition-all flex items-center justify-center gap-2 hover:border-purple-500/50 text-sm md:text-base">
                <Play className="w-4 md:w-5 h-4 md:h-5" />
                <span className="hidden sm:inline">See Multi-Agent Demo</span>
                <span className="sm:hidden">Demo</span>
              </button>
            </div>

            {/* Value Props */}
            <div className="flex flex-wrap justify-center items-center gap-6 md:gap-8 text-slate-400 text-sm">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-400" />
                <span>50+ AI Components</span>
              </div>
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-cyan-400" />
                <span>Multi-Agent Teams</span>
              </div>
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-green-400" />
                <span>Full Observability</span>
              </div>
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-yellow-400" />
                <span>Enterprise Security</span>
              </div>
              <div className="flex items-center gap-2">
                <Rocket className="w-4 h-4 text-pink-400" />
                <span>One-Click Deploy</span>
              </div>
            </div>
          </div>

          {/* Hero Visual - Multi-Agent Orchestration Demo */}
          <div className="relative">
            <div className="bg-gradient-to-br from-slate-900/50 to-purple-900/20 rounded-2xl border border-purple-500/20 p-8 backdrop-blur-xl">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                  <span className="text-slate-400 text-sm">nodai.io/workflows/customer-support-agents</span>
                </div>
                <div className="flex items-center gap-2 text-green-400 text-sm">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span>Live Demo</span>
                </div>
              </div>
              
              {/* Multi-Agent Canvas */}
              <div className="bg-slate-950 rounded-lg p-6 min-h-[500px] relative overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_70%,_theme(colors.purple.500/15),_transparent_60%),radial-gradient(circle_at_70%_30%,_theme(colors.cyan.500/15),_transparent_60%)]"></div>
                
                {/* Agent Orchestration Flow */}
                <div className="relative z-10 h-full">
                  {/* Input Layer */}
                  <div className="mb-8">
                    <div className="text-xs text-slate-500 mb-3">Customer Input</div>
                    <div className="bg-gradient-to-r from-blue-500/20 to-indigo-500/20 border border-blue-500/30 rounded-lg p-3 inline-block">
                      <div className="flex items-center gap-3">
                        <Database className="w-6 h-6 text-blue-400" />
                        <div className="text-sm text-blue-300">"Help me process a refund for order #12345"</div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Agent Layer */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                    {/* Classifier Agent */}
                    <div className="bg-gradient-to-br from-purple-500/20 to-violet-500/20 border border-purple-500/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-8 h-8 bg-purple-500/30 rounded-full flex items-center justify-center">
                          <Brain className="w-4 h-4 text-purple-300" />
                        </div>
                        <div>
                          <div className="text-sm text-purple-300 font-semibold">Classifier Agent</div>
                          <div className="text-xs text-slate-500">Intent Recognition</div>
                        </div>
                      </div>
                      <div className="bg-slate-900/50 rounded p-2 mb-2">
                        <div className="text-xs text-slate-400">Classification: Refund Request</div>
                        <div className="text-xs text-purple-300">Confidence: 94%</div>
                      </div>
                      <div className="flex items-center gap-1 text-xs">
                        <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
                        <span className="text-green-400">Processing</span>
                      </div>
                    </div>

                    {/* Data Retrieval Agent */}
                    <div className="bg-gradient-to-br from-cyan-500/20 to-teal-500/20 border border-cyan-500/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-8 h-8 bg-cyan-500/30 rounded-full flex items-center justify-center">
                          <Database className="w-4 h-4 text-cyan-300" />
                        </div>
                        <div>
                          <div className="text-sm text-cyan-300 font-semibold">Data Agent</div>
                          <div className="text-xs text-slate-500">Order Lookup</div>
                        </div>
                      </div>
                      <div className="bg-slate-900/50 rounded p-2 mb-2">
                        <div className="text-xs text-slate-400">Order #12345 found</div>
                        <div className="text-xs text-cyan-300">Status: Delivered</div>
                      </div>
                      <div className="flex items-center gap-1 text-xs">
                        <div className="w-1.5 h-1.5 bg-yellow-400 rounded-full animate-pulse"></div>
                        <span className="text-yellow-400">Retrieving</span>
                      </div>
                    </div>

                    {/* Response Agent */}
                    <div className="bg-gradient-to-br from-emerald-500/20 to-green-500/20 border border-emerald-500/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-8 h-8 bg-emerald-500/30 rounded-full flex items-center justify-center">
                          <Users className="w-4 h-4 text-emerald-300" />
                        </div>
                        <div>
                          <div className="text-sm text-emerald-300 font-semibold">Response Agent</div>
                          <div className="text-xs text-slate-500">Customer Reply</div>
                        </div>
                      </div>
                      <div className="bg-slate-900/50 rounded p-2 mb-2">
                        <div className="text-xs text-slate-400">Crafting personalized response...</div>
                      </div>
                      <div className="flex items-center gap-1 text-xs">
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse"></div>
                        <span className="text-blue-400">Generating</span>
                      </div>
                    </div>
                  </div>

                  {/* Output Layer */}
                  <div className="mb-4">
                    <div className="text-xs text-slate-500 mb-3">Intelligent Response</div>
                    <div className="bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/30 rounded-lg p-4">
                      <div className="text-sm text-emerald-300 mb-2">
                        "I've located order #12345. Since it was delivered within our 30-day return window, I've initiated your refund of $89.99. 
                        You'll see the credit within 3-5 business days. Is there anything else I can help with?"
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-4 text-slate-500">
                          <span>Response time: 2.3s</span>
                          <span>Confidence: 98%</span>
                          <span>Cost: $0.012</span>
                        </div>
                        <div className="flex items-center gap-1 text-green-400">
                          <CheckCircle className="w-3 h-3" />
                          <span>Resolved</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Performance Metrics */}
                <div className="absolute top-4 right-4 bg-slate-900/80 backdrop-blur border border-purple-500/30 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-2">Real-time Metrics</div>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Agents Active:</span>
                      <span className="text-purple-400">3/3</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Avg Response:</span>
                      <span className="text-cyan-400">2.1s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Success Rate:</span>
                      <span className="text-green-400">97.8%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Industry Use Cases Section */}
      <section id="industries" className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-900/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-6">
              Powering AI Across
              <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent"> Every Industry</span>
            </h2>
            <p className="text-xl text-slate-400 max-w-3xl mx-auto">
              From startups to Fortune 500, teams are building intelligent systems that actually work
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* FinTech */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 hover:border-purple-500/30 transition-all hover:scale-105">
              <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mb-4">
                <DollarSign className="w-6 h-6 text-green-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-green-400">FinTech</h3>
              <p className="text-slate-400 mb-4">
                Document processing, fraud detection, risk analysis. Multi-agent teams that handle complex financial workflows.
              </p>
              <div className="text-sm text-purple-300">• Loan processing automation • KYC document verification • Trading signal analysis</div>
            </div>

            {/* Healthcare */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 hover:border-cyan-500/30 transition-all hover:scale-105">
              <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-blue-400">Healthcare</h3>
              <p className="text-slate-400 mb-4">
                Medical record analysis, patient data processing, diagnostic support with multi-modal AI workflows.
              </p>
              <div className="text-sm text-cyan-300">• Medical imaging analysis • Clinical note processing • Drug interaction detection</div>
            </div>

            {/* E-commerce */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 hover:border-yellow-500/30 transition-all hover:scale-105">
              <div className="w-12 h-12 bg-yellow-500/20 rounded-lg flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-yellow-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-yellow-400">E-commerce</h3>
              <p className="text-slate-400 mb-4">
                Recommendation engines, product catalog management, customer support automation at scale.
              </p>
              <div className="text-sm text-yellow-300">• Personalized recommendations • Inventory optimization • Visual search</div>
            </div>

            {/* Customer Support */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 hover:border-emerald-500/30 transition-all hover:scale-105">
              <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-emerald-400">Customer Support</h3>
              <p className="text-slate-400 mb-4">
                Intelligent chatbots, ticket routing, sentiment analysis with real-time human handoff.
              </p>
              <div className="text-sm text-emerald-300">• Multi-language support • Escalation routing • Knowledge mining</div>
            </div>

            {/* Legal */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 hover:border-indigo-500/30 transition-all hover:scale-105">
              <div className="w-12 h-12 bg-indigo-500/20 rounded-lg flex items-center justify-center mb-4">
                <Lock className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-indigo-400">Legal</h3>
              <p className="text-slate-400 mb-4">
                Contract analysis, document review automation, legal research with citation verification.
              </p>
              <div className="text-sm text-indigo-300">• Contract clause extraction • Due diligence • Regulatory compliance</div>
            </div>

            {/* Content Creation */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 hover:border-pink-500/30 transition-all hover:scale-105">
              <div className="w-12 h-12 bg-pink-500/20 rounded-lg flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-pink-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-pink-400">Media & Content</h3>
              <p className="text-slate-400 mb-4">
                Multi-modal content generation, video analysis, automated storytelling workflows.
              </p>
              <div className="text-sm text-pink-300">• Video summarization • Content personalization • Brand voice consistency</div>
            </div>
          </div>

          {/* Stats Bar */}
          <div className="mt-16 bg-gradient-to-r from-purple-900/20 to-cyan-900/20 rounded-2xl border border-purple-500/20 p-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl font-bold text-purple-400 mb-2">500+</div>
                <div className="text-slate-400 text-sm">Enterprise Customers</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-cyan-400 mb-2">50M+</div>
                <div className="text-slate-400 text-sm">Workflows Executed</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-400 mb-2">85%</div>
                <div className="text-slate-400 text-sm">Cost Reduction Avg</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-yellow-400 mb-2">2.3s</div>
                <div className="text-slate-400 text-sm">Avg Response Time</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Platform Capabilities Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-6">
              The Complete
              <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent"> GenAI Development Stack</span>
            </h2>
            <p className="text-xl text-slate-400 max-w-4xl mx-auto">
              From prompt engineering to multi-agent orchestration. From fine-tuning to production monitoring. 
              Everything you need to build intelligent systems that actually work.
            </p>
          </div>

          {/* Multi-Agent Orchestration */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-20">
            <div>
              <div className="inline-flex items-center gap-2 bg-purple-500/10 border border-purple-500/20 rounded-full px-4 py-2 mb-6">
                <Users className="w-4 h-4 text-purple-400" />
                <span className="text-sm text-purple-300">Multi-Agent Teams</span>
              </div>
              <h3 className="text-3xl font-bold mb-4">CrewAI-Powered Agent Orchestration</h3>
              <p className="text-slate-400 mb-6 leading-relaxed">
                Build teams of specialized AI agents that collaborate intelligently. Define roles, goals, and workflows 
                visually. Watch your agents work together like a real team.
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Drag-and-drop agent creation</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Role-based task delegation</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Real-time collaboration monitoring</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>CrewAI + LangChain integration</span>
                </li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-slate-900 to-purple-900/20 rounded-xl p-6 border border-purple-500/20">
              <div className="bg-slate-950 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-4">Agent Team Configuration</div>
                <div className="space-y-4">
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 bg-purple-500/30 rounded-full flex items-center justify-center">
                        <Brain className="w-3 h-3 text-purple-300" />
                      </div>
                      <span className="text-sm text-purple-300 font-semibold">Research Agent</span>
                    </div>
                    <div className="text-xs text-slate-400">Role: Data Analyst</div>
                    <div className="text-xs text-slate-400">Goal: Gather market insights</div>
                  </div>
                  <div className="bg-cyan-500/10 border border-cyan-500/30 rounded p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 bg-cyan-500/30 rounded-full flex items-center justify-center">
                        <Users className="w-3 h-3 text-cyan-300" />
                      </div>
                      <span className="text-sm text-cyan-300 font-semibold">Content Agent</span>
                    </div>
                    <div className="text-xs text-slate-400">Role: Content Creator</div>
                    <div className="text-xs text-slate-400">Goal: Generate reports</div>
                  </div>
                  <div className="bg-green-500/10 border border-green-500/30 rounded p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 bg-green-500/30 rounded-full flex items-center justify-center">
                        <CheckCircle className="w-3 h-3 text-green-300" />
                      </div>
                      <span className="text-sm text-green-300 font-semibold">QA Agent</span>
                    </div>
                    <div className="text-xs text-slate-400">Role: Quality Assurance</div>
                    <div className="text-xs text-slate-400">Goal: Validate outputs</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Prompt Engineering & Fine-tuning */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-20">
            <div className="order-2 lg:order-1">
              <div className="bg-gradient-to-br from-slate-900 to-cyan-900/20 rounded-xl p-6 border border-cyan-500/20">
                <div className="bg-slate-950 rounded-lg p-4">
                  <div className="text-sm text-slate-400 mb-4">Prompt Playground</div>
                  <div className="space-y-3">
                    <div className="bg-slate-800 rounded p-3">
                      <div className="text-xs text-cyan-400 mb-1">System Prompt</div>
                      <div className="text-xs text-slate-300">You are an expert financial analyst...</div>
                    </div>
                    <div className="bg-slate-800 rounded p-3">
                      <div className="text-xs text-purple-400 mb-1">User Input</div>
                      <div className="text-xs text-slate-300">Analyze Q3 revenue trends for SAAS company</div>
                    </div>
                    <div className="bg-emerald-500/10 border border-emerald-500/30 rounded p-3">
                      <div className="text-xs text-emerald-400 mb-1">Generated Response</div>
                      <div className="text-xs text-slate-300">Based on the data provided, Q3 shows...</div>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <div className="text-slate-500">Latency: 1.2s</div>
                      <div className="text-green-400">Cost: $0.0045</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <div className="inline-flex items-center gap-2 bg-cyan-500/10 border border-cyan-500/20 rounded-full px-4 py-2 mb-6">
                <Code className="w-4 h-4 text-cyan-400" />
                <span className="text-sm text-cyan-300">Prompt Engineering</span>
              </div>
              <h3 className="text-3xl font-bold mb-4">Perfect Your Prompts Visually</h3>
              <p className="text-slate-400 mb-6 leading-relaxed">
                Interactive prompt playground with A/B testing, version control, and performance analytics. 
                Fine-tune models with custom datasets. Export optimized prompts directly to production.
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Real-time prompt testing & optimization</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>A/B test different prompt variations</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Custom model fine-tuning workflows</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Performance & cost analytics</span>
                </li>
              </ul>
            </div>
          </div>

          {/* 50+ Components Ecosystem */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-20">
            <div>
              <div className="inline-flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-full px-4 py-2 mb-6">
                <Workflow className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-300">50+ Components</span>
              </div>
              <h3 className="text-3xl font-bold mb-4">Every AI Component You Need</h3>
              <p className="text-slate-400 mb-6 leading-relaxed">
                From basic text processing to advanced multi-modal AI. LangChain integrations, 
                vector databases, LLM providers, and custom tools. Build anything with drag-and-drop.
              </p>
              <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="bg-slate-800/50 rounded p-3 text-center">
                  <Database className="w-6 h-6 text-blue-400 mx-auto mb-1" />
                  <div className="text-xs text-blue-300">Data Sources</div>
                  <div className="text-xs text-slate-500">Files, APIs, DBs</div>
                </div>
                <div className="bg-slate-800/50 rounded p-3 text-center">
                  <Brain className="w-6 h-6 text-purple-400 mx-auto mb-1" />
                  <div className="text-xs text-purple-300">Processing</div>
                  <div className="text-xs text-slate-500">NLP, OCR, Vision</div>
                </div>
                <div className="bg-slate-800/50 rounded p-3 text-center">
                  <Cpu className="w-6 h-6 text-cyan-400 mx-auto mb-1" />
                  <div className="text-xs text-cyan-300">LLMs</div>
                  <div className="text-xs text-slate-500">GPT, Claude, Gemini</div>
                </div>
                <div className="bg-slate-800/50 rounded p-3 text-center">
                  <Users className="w-6 h-6 text-green-400 mx-auto mb-1" />
                  <div className="text-xs text-green-300">Agents</div>
                  <div className="text-xs text-slate-500">CrewAI, Custom</div>
                </div>
              </div>
            </div>
            <div className="bg-gradient-to-br from-slate-900 to-green-900/20 rounded-xl p-6 border border-green-500/20">
              <div className="bg-slate-950 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-4">Node Library</div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded p-2">
                    <div className="text-blue-300 font-semibold">Input (8)</div>
                    <div className="text-slate-400">File, Text, Webhook, API</div>
                  </div>
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded p-2">
                    <div className="text-purple-300 font-semibold">Processing (12)</div>
                    <div className="text-slate-400">Chunk, OCR, Transcribe</div>
                  </div>
                  <div className="bg-cyan-500/10 border border-cyan-500/30 rounded p-2">
                    <div className="text-cyan-300 font-semibold">LLM (10)</div>
                    <div className="text-slate-400">Chat, Vision, Embeddings</div>
                  </div>
                  <div className="bg-green-500/10 border border-green-500/30 rounded p-2">
                    <div className="text-green-300 font-semibold">Tools (15)</div>
                    <div className="text-slate-400">Search, DB, Custom</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Observability & Production Features Section */}
      <section id="observability" className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-900/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-6">
              Production-Ready
              <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent"> Features</span>
            </h2>
            <p className="text-xl text-slate-400 max-w-4xl mx-auto">
              Enterprise-grade observability, security, and deployment. Everything you need to run AI systems in production.
            </p>
          </div>

          {/* Observability & Monitoring */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-20">
            <div>
              <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-4 py-2 mb-6">
                <Eye className="w-4 h-4 text-emerald-400" />
                <span className="text-sm text-emerald-300">Full Observability</span>
              </div>
              <h3 className="text-3xl font-bold mb-4">See Every Token, Track Every Cost</h3>
              <p className="text-slate-400 mb-6 leading-relaxed">
                End-to-end execution traces, span-level performance metrics, and AI-powered cost forecasting. 
                Debug faster, optimize smarter, and forecast expenses with confidence.
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>End-to-end execution traces</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Cost forecasting based on historical data</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Span-level performance metrics</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>LangSmith & LangFuse integration</span>
                </li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-slate-900 to-emerald-900/20 rounded-xl p-6 border border-emerald-500/20">
              <div className="bg-slate-950 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-4">Trace Visualization</div>
                <div className="space-y-3">
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-emerald-300 font-semibold">Query Processing</span>
                      <span className="text-xs text-slate-400">1.2s</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: '100%' }}></div>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">Cost: $0.0045 | Tokens: 1,234</div>
                  </div>
                  <div className="bg-cyan-500/10 border border-cyan-500/30 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-cyan-300 font-semibold">Vector Search</span>
                      <span className="text-xs text-slate-400">0.3s</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-cyan-500 rounded-full" style={{ width: '25%' }}></div>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">Cost: $0.0001 | Results: 5</div>
                  </div>
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-purple-300 font-semibold">LLM Generation</span>
                      <span className="text-xs text-slate-400">0.8s</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500 rounded-full" style={{ width: '67%' }}></div>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">Cost: $0.0032 | Tokens: 856</div>
                  </div>
                  <div className="bg-slate-800/50 rounded p-2 mt-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Forecasted Monthly Cost:</span>
                      <span className="text-emerald-400 font-semibold">$1,247</span>
                    </div>
                    <div className="flex items-center gap-1 mt-1">
                      <TrendingUp className="w-3 h-3 text-green-400" />
                      <span className="text-xs text-green-400">+12% vs last month</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Enterprise Security */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-20">
            <div className="order-2 lg:order-1">
              <div className="bg-gradient-to-br from-slate-900 to-yellow-900/20 rounded-xl p-6 border border-yellow-500/20">
                <div className="bg-slate-950 rounded-lg p-4">
                  <div className="text-sm text-slate-400 mb-4">Secrets Vault</div>
                  <div className="space-y-3">
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Key className="w-4 h-4 text-yellow-400" />
                          <span className="text-xs text-yellow-300 font-semibold">OpenAI API Key</span>
                        </div>
                        <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      </div>
                      <div className="text-xs text-slate-400">Encrypted • Last used 2h ago</div>
                    </div>
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Key className="w-4 h-4 text-yellow-400" />
                          <span className="text-xs text-yellow-300 font-semibold">Anthropic API Key</span>
                        </div>
                        <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      </div>
                      <div className="text-xs text-slate-400">Encrypted • Last used 5m ago</div>
                    </div>
                    <div className="bg-slate-800/50 rounded p-2 mt-3">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">Multi-tenant isolation:</span>
                        <span className="text-green-400 font-semibold">✓ Enabled</span>
                      </div>
                      <div className="flex items-center justify-between text-xs mt-1">
                        <span className="text-slate-400">Encryption:</span>
                        <span className="text-green-400 font-semibold">AES-256</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <div className="inline-flex items-center gap-2 bg-yellow-500/10 border border-yellow-500/20 rounded-full px-4 py-2 mb-6">
                <Shield className="w-4 h-4 text-yellow-400" />
                <span className="text-sm text-yellow-300">Enterprise Security</span>
              </div>
              <h3 className="text-3xl font-bold mb-4">Bank-Grade Security Built In</h3>
              <p className="text-slate-400 mb-6 leading-relaxed">
                Encrypted secrets vault, multi-tenant isolation, and SOC2-ready architecture. 
                Your API keys are encrypted at rest, isolated per tenant, and never exposed in logs.
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Encrypted secrets vault (AES-256)</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Multi-tenant data isolation</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>SOC2-ready architecture</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Zero-trust API key management</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Deployment & Production */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-20">
            <div>
              <div className="inline-flex items-center gap-2 bg-pink-500/10 border border-pink-500/20 rounded-full px-4 py-2 mb-6">
                <Rocket className="w-4 h-4 text-pink-400" />
                <span className="text-sm text-pink-300">Deployment</span>
              </div>
              <h3 className="text-3xl font-bold mb-4">Deploy to Production in Minutes</h3>
              <p className="text-slate-400 mb-6 leading-relaxed">
                One-click workflow deployment, version control with rollbacks, and production API endpoints. 
                Deploy instantly, monitor continuously, and scale effortlessly.
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>One-click workflow deployment</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Version control & instant rollbacks</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Webhook endpoints for integrations</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Production API access</span>
                </li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-slate-900 to-pink-900/20 rounded-xl p-6 border border-pink-500/20">
              <div className="bg-slate-950 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-4">Deployment Dashboard</div>
                <div className="space-y-3">
                  <div className="bg-pink-500/10 border border-pink-500/30 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-pink-300 font-semibold">Customer Support Bot</span>
                      <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Active</span>
                    </div>
                    <div className="text-xs text-slate-400">Version 3.2.1 • Deployed 2h ago</div>
                    <div className="flex items-center gap-4 mt-2 text-xs">
                      <span className="text-slate-500">Queries: 1,247</span>
                      <span className="text-green-400">Success: 99.8%</span>
                    </div>
                  </div>
                  <div className="bg-slate-800/50 border border-slate-700 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-slate-300 font-semibold">Document Processor</span>
                      <span className="text-xs bg-slate-700 text-slate-400 px-2 py-1 rounded">v2.1.0</span>
                    </div>
                    <div className="text-xs text-slate-500">Last deployed 3d ago</div>
                  </div>
                  <div className="bg-slate-800/50 border border-slate-700 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-slate-300 font-semibold">RAG Knowledge Base</span>
                      <span className="text-xs bg-slate-700 text-slate-400 px-2 py-1 rounded">v1.5.2</span>
                    </div>
                    <div className="text-xs text-slate-500">Last deployed 1w ago</div>
                  </div>
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded p-2 mt-3">
                    <div className="flex items-center gap-2 text-xs">
                      <Cloud className="w-3 h-3 text-blue-400" />
                      <span className="text-blue-300">Webhook: api.nodai.io/webhook/abc123</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Knowledge Bases & RAG */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-20">
            <div className="order-2 lg:order-1">
              <div className="bg-gradient-to-br from-slate-900 to-blue-900/20 rounded-xl p-6 border border-blue-500/20">
                <div className="bg-slate-950 rounded-lg p-4">
                  <div className="text-sm text-slate-400 mb-4">Knowledge Base</div>
                  <div className="space-y-3">
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="w-4 h-4 text-blue-400" />
                        <span className="text-xs text-blue-300 font-semibold">Company Docs</span>
                      </div>
                      <div className="text-xs text-slate-400">5,247 documents • 12,456 chunks</div>
                      <div className="flex items-center gap-2 mt-2">
                        <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                        <span className="text-xs text-green-400">Processing complete</span>
                      </div>
                    </div>
                    <div className="bg-slate-800/50 rounded p-2">
                      <div className="text-xs text-slate-400 mb-1">Hybrid Search Enabled</div>
                      <div className="flex items-center gap-2 text-xs">
                        <Search className="w-3 h-3 text-cyan-400" />
                        <span className="text-cyan-300">Semantic + BM25 + Graph</span>
                      </div>
                    </div>
                    <div className="bg-purple-500/10 border border-purple-500/30 rounded p-2">
                      <div className="text-xs text-purple-300 font-semibold mb-1">Query Performance</div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">Avg latency:</span>
                        <span className="text-green-400">0.8s</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">Relevance score:</span>
                        <span className="text-green-400">94%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-2 mb-6">
                <BookOpen className="w-4 h-4 text-blue-400" />
                <span className="text-sm text-blue-300">Knowledge Bases</span>
              </div>
              <h3 className="text-3xl font-bold mb-4">Build Production RAG Systems</h3>
              <p className="text-slate-400 mb-6 leading-relaxed">
                Process 5000+ documents, build knowledge bases, and deploy hybrid search with semantic, 
                BM25, and knowledge graph queries. Enterprise-scale document processing pipelines.
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Knowledge base management</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>3-way hybrid search (semantic + BM25 + graph)</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Document processing pipelines</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Enterprise-scale ingestion</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Fine-tuning */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-20">
            <div>
              <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-2 mb-6">
                <Settings className="w-4 h-4 text-indigo-400" />
                <span className="text-sm text-indigo-300">Fine-Tuning</span>
              </div>
              <h3 className="text-3xl font-bold mb-4">Train Your Own Models</h3>
              <p className="text-slate-400 mb-6 leading-relaxed">
                Fine-tune LLMs on your data, create custom models, and maintain brand voice consistency. 
                Custom model training workflows with full control over training parameters.
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Fine-tune LLMs on your data</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Custom model training workflows</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Model registry & management</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Brand voice consistency</span>
                </li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-slate-900 to-indigo-900/20 rounded-xl p-6 border border-indigo-500/20">
              <div className="bg-slate-950 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-4">Model Training</div>
                <div className="space-y-3">
                  <div className="bg-indigo-500/10 border border-indigo-500/30 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-indigo-300 font-semibold">Customer Support Model</span>
                      <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Trained</span>
                    </div>
                    <div className="text-xs text-slate-400">Base: GPT-4 • Epochs: 3 • Accuracy: 96%</div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden mt-2">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: '96%' }}></div>
                    </div>
                  </div>
                  <div className="bg-slate-800/50 border border-slate-700 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-slate-300 font-semibold">Legal Document Analyzer</span>
                      <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">Training</span>
                    </div>
                    <div className="text-xs text-slate-400">Base: Claude-3 • Epochs: 2/5 • Progress: 40%</div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden mt-2">
                      <div className="h-full bg-yellow-500 rounded-full" style={{ width: '40%' }}></div>
                    </div>
                  </div>
                  <div className="bg-slate-800/50 rounded p-2 mt-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Training dataset:</span>
                      <span className="text-indigo-400 font-semibold">12,456 examples</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-6">
              Trusted by Teams Building the Future
            </h2>
            <p className="text-xl text-slate-400">Join the GenAI engineers who've already saved millions</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-full flex items-center justify-center text-white font-semibold">
                  SX
                </div>
                <div>
                  <div className="font-semibold">Sarah Chen</div>
                  <div className="text-sm text-slate-400">Staff AI Engineer, Scale AI</div>
                </div>
              </div>
              <p className="text-slate-300 mb-4">
                "NodAI cut our RAG development time from 3 months to 2 weeks. The cost insights alone saved us $50K+ last quarter."
              </p>
              <div className="flex text-yellow-400">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-current" />
                ))}
              </div>
            </div>

            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                  MR
                </div>
                <div>
                  <div className="font-semibold">Marcus Rodriguez</div>
                  <div className="text-sm text-slate-400">AI Platform Lead, Stripe</div>
                </div>
              </div>
              <p className="text-slate-300 mb-4">
                "Finally, a platform that understands what we actually need. Visual debugging + cost optimization in one place. Game changer."
              </p>
              <div className="flex text-yellow-400">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-current" />
                ))}
              </div>
            </div>

            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center text-white font-semibold">
                  AK
                </div>
                <div>
                  <div className="font-semibold">Aisha Kumar</div>
                  <div className="text-sm text-slate-400">Senior ML Engineer, Databricks</div>
                </div>
              </div>
              <p className="text-slate-300 mb-4">
                "The visual workflow builder is incredible. My team went from code-first to visual-first in a week. Productivity 10x'd."
              </p>
              <div className="flex text-yellow-400">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-current" />
                ))}
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-purple-400 mb-2">60%</div>
              <div className="text-slate-400">Average Cost Reduction</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-cyan-400 mb-2">10x</div>
              <div className="text-slate-400">Faster Development</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-green-400 mb-2">99.9%</div>
              <div className="text-slate-400">Uptime SLA</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-yellow-400 mb-2">1M+</div>
              <div className="text-slate-400">Workflows Deployed</div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-6">
              Start Free, Scale When Ready
            </h2>
            <p className="text-xl text-slate-400">No credit card required. Build unlimited workflows on the free tier.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Developer Plan */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 border border-slate-700">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-2">Developer</h3>
                <div className="text-4xl font-bold mb-2">Free</div>
                <p className="text-slate-400">Perfect for getting started</p>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>5 workflows</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>1,000 executions/month</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Basic cost tracking</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Community support</span>
                </li>
              </ul>
              <Link 
                to="/register"
                className="w-full bg-slate-700 hover:bg-slate-600 px-6 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center"
              >
                Start Free
              </Link>
            </div>

            {/* Pro Plan */}
            <div className="bg-gradient-to-br from-purple-500/10 to-cyan-500/10 rounded-2xl p-8 border border-purple-500/30 relative">
              <div className="absolute top-4 right-4 bg-gradient-to-r from-purple-500 to-cyan-500 text-white text-xs px-3 py-1 rounded-full">
                Most Popular
              </div>
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-2">Pro</h3>
                <div className="text-4xl font-bold mb-2">
                  $49<span className="text-lg text-slate-400">/month</span>
                </div>
                <p className="text-slate-400">For serious builders</p>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Unlimited workflows</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>50K executions/month</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Advanced cost optimization</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Priority support</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Code export</span>
                </li>
              </ul>
              <Link 
                to="/register"
                className="w-full bg-gradient-to-r from-purple-500 to-cyan-500 hover:shadow-lg hover:shadow-purple-500/25 px-6 py-3 rounded-lg font-semibold transition-all flex items-center justify-center"
              >
                Start 14-Day Trial
              </Link>
            </div>

            {/* Enterprise Plan */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 border border-slate-700">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-2">Enterprise</h3>
                <div className="text-4xl font-bold mb-2">Custom</div>
                <p className="text-slate-400">For teams at scale</p>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Unlimited everything</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>On-premise deployment</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>Custom integrations</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>24/7 dedicated support</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span>SLA guarantees</span>
                </li>
              </ul>
              <button className="w-full border border-slate-600 hover:bg-slate-700 px-6 py-3 rounded-lg font-semibold transition-colors">
                Contact Sales
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-purple-900/20 to-cyan-900/20">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-3xl md:text-5xl font-bold mb-6">
            Ready to Build Smarter AI?
          </h2>
          <p className="text-xl text-slate-400 mb-8 max-w-3xl mx-auto">
            Join thousands of GenAI engineers who are already building faster, cheaper, and more reliable AI workflows.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link 
              to="/register"
              className="bg-gradient-to-r from-purple-500 to-cyan-500 px-8 py-4 rounded-lg text-white font-semibold hover:shadow-lg hover:shadow-purple-500/25 transition-all flex items-center justify-center gap-2 group"
            >
              Start Building Free
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <button className="border border-slate-600 px-8 py-4 rounded-lg text-white font-semibold hover:bg-slate-800 transition-colors">
              Schedule Demo
            </button>
          </div>

          <div className="flex flex-wrap justify-center items-center gap-8 text-slate-500 text-sm">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span>Free forever plan</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span>5-minute setup</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-slate-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg flex items-center justify-center">
                <Workflow className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                NodAI
              </span>
            </div>
            
            <div className="flex items-center space-x-6 text-slate-400">
              <a href="mailto:hello@nodai.io" className="hover:text-white transition-colors">Contact</a>
              <a href="/docs" className="hover:text-white transition-colors">Docs</a>
              <a href="https://github.com/nodai" className="hover:text-white transition-colors flex items-center gap-2">
                <Github className="w-4 h-4" />
                GitHub
              </a>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-slate-800 text-center text-slate-500 text-sm">
            <p>&copy; 2025 NodAI. Built with ❤️ for the GenAI community.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}