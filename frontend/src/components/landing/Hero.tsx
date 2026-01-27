import { Link } from 'react-router-dom';
import { ArrowRight, Play, CheckCircle, TrendingDown, Zap, Brain } from 'lucide-react';
import { motion } from 'framer-motion';

export function Hero() {
    return (
        <section className="relative py-32 md:py-48 flex flex-col justify-center items-center text-center px-4 sm:px-6 lg:px-8 overflow-hidden">
            <div className="max-w-7xl mx-auto relative z-10">
                {/* Badge */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="inline-flex items-center gap-2 px-4 py-2 pl-2 bg-green-500/10 border border-green-500/30 rounded-full mb-8"
                >
                    <TrendingDown className="w-4 h-4 text-green-400" />
                    <span className="text-sm font-medium text-green-400">
                        Cut AI Costs by 70% with Intelligent Model Routing
                    </span>
                </motion.div>

                {/* Main Heading */}
                <motion.h1
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1 }}
                    className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight mb-6 leading-[1.05] max-w-5xl mx-auto"
                >
                    RAG + Fine-Tuning + <br />
                    <span className="bg-gradient-to-r from-amber-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent bg-[length:200%_200%] animate-gradient">
                        Multi-Agent
                    </span>
                    <br />
                    One Platform
                </motion.h1>

                {/* Subtitle */}
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="text-lg md:text-xl text-slate-400 mb-8 max-w-2xl mx-auto leading-relaxed"
                >
                    Build production-ready RAG pipelines, orchestrate multi-agent systems with CrewAI,
                    and optimize costs with real-time tracking. No code required.
                </motion.p>

                {/* Value Props */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.25 }}
                    className="flex flex-wrap items-center justify-center gap-6 mb-12 text-sm"
                >
                    <div className="flex items-center gap-2 text-slate-300">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span>Vector DB Integration</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span>CrewAI + LangChain</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span>Cost Per Token Tracking</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span>Full Observability</span>
                    </div>
                </motion.div>

                {/* CTA Buttons */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                    className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20"
                >
                    <Link
                        to="/register"
                        className="group relative px-8 py-4 bg-gradient-to-r from-amber-500 to-orange-600 text-slate-950 rounded-xl font-bold text-lg transition-all hover:scale-105 hover:shadow-2xl hover:shadow-amber-500/40 flex items-center gap-2 overflow-hidden"
                    >
                        <span className="relative z-10">Start Building Free →</span>
                        <div className="absolute inset-0 bg-gradient-to-r from-amber-400 to-amber-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </Link>
                    <button className="px-8 py-4 bg-transparent border border-slate-700 text-white rounded-xl font-semibold text-lg transition-all hover:bg-slate-800/50 hover:border-slate-600 flex items-center gap-2">
                        <Play className="w-5 h-5" />
                        Watch Demo
                    </button>
                </motion.div>

                {/* Visual Placeholder */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.8, delay: 0.4 }}
                    className="relative max-w-5xl mx-auto"
                >
                    <div className="relative rounded-3xl overflow-hidden border border-slate-800 shadow-2xl shadow-amber-500/10">
                        {/* Animated Border */}
                        <div className="absolute inset-0 rounded-3xl p-[2px] bg-gradient-to-r from-amber-500 via-pink-500 to-cyan-500 opacity-50 animate-gradient-x">
                            <div className="w-full h-full bg-slate-900 rounded-3xl" />
                        </div>

                        {/* Content - Video */}
                        <div className="relative aspect-video">
                            <video
                                autoPlay
                                loop
                                muted
                                playsInline
                                className="w-full h-full object-cover"
                            >
                                <source src="/videos/hero-workflow.mp4" type="video/mp4" />
                                {/* Fallback image */}
                                <img 
                                    src="/images/hero-workflow-fallback.jpg" 
                                    alt="NodeAI Workflow Demo" 
                                    className="w-full h-full object-cover"
                                />
                            </video>
                        </div>
                    </div>

                    {/* Floating Nodes */}
                    <FloatingNode
                        icon="🧠"
                        label="RAG Pipeline"
                        position="top-10 -left-20"
                        delay={0.6}
                    />
                    <FloatingNode
                        icon="💰"
                        label="Cost: $0.0012"
                        position="top-1/3 -right-24"
                        delay={0.7}
                    />
                    <FloatingNode
                        icon="🤖"
                        label="CrewAI Multi-Agent"
                        position="bottom-20 -left-16"
                        delay={0.8}
                    />
                    <FloatingNode
                        icon="📊"
                        label="Pinecone + FAISS"
                        position="bottom-10 -right-20"
                        delay={0.9}
                    />
                </motion.div>
            </div>
        </section>
    );
}

function FloatingNode({
    icon,
    label,
    position,
    delay,
}: {
    icon: string;
    label: string;
    position: string;
    delay: number;
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay }}
            className={`absolute ${position} hidden lg:block`}
        >
            <motion.div
                animate={{ y: [0, -15, 0] }}
                transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                className="flex items-center gap-3 bg-slate-900/90 backdrop-blur-sm border border-slate-800 rounded-xl px-4 py-3 shadow-xl"
            >
                <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-lg">
                    {icon}
                </div>
                <span className="text-sm font-semibold text-white whitespace-nowrap">{label}</span>
            </motion.div>
        </motion.div>
    );
}

