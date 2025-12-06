import { Link } from 'react-router-dom';
import { ArrowRight, Play, CheckCircle, Database, Brain, Zap } from 'lucide-react';
import { motion, useScroll, useTransform, useMotionValue, useSpring } from 'framer-motion';
import { useRef } from 'react';

export function Hero() {
    const ref = useRef(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ["start start", "end start"]
    });

    return (
        <section ref={ref} className="relative pt-32 pb-20 md:pt-48 md:pb-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
            {/* Background Gradients */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full max-w-7xl pointer-events-none">
                <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-indigo-500/20 rounded-full blur-[120px]" />
                <div className="absolute top-[10%] right-[-10%] w-[400px] h-[400px] bg-cyan-500/20 rounded-full blur-[100px]" />
            </div>

            <div className="max-w-7xl mx-auto relative z-10">
                <div className="flex flex-col lg:flex-row items-center gap-16">

                    {/* Text Content */}
                    <div className="flex-1 text-center lg:text-left">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="inline-flex items-center gap-2 bg-slate-900/50 border border-slate-800 rounded-full px-4 py-1.5 mb-8 backdrop-blur-sm"
                        >
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                            <span className="text-sm font-medium text-slate-300">v2.0 is now live</span>
                        </motion.div>

                        <motion.h1
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.1 }}
                            className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6 leading-[1.1]"
                        >
                            Build AI Agents <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-400 to-green-400">
                                With Engineering Precision
                            </span>
                        </motion.h1>

                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                            className="text-lg md:text-xl text-slate-400 mb-8 max-w-2xl mx-auto lg:mx-0 leading-relaxed"
                        >
                            The first visual workflow builder designed for production.
                            Orchestrate multi-agent systems with full observability, type safety, and enterprise security.
                        </motion.p>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.3 }}
                            className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start"
                        >
                            <Link
                                to="/register"
                                className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-xl font-semibold transition-all hover:scale-105 flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/25"
                            >
                                Start Building Free
                                <ArrowRight className="w-4 h-4" />
                            </Link>
                            <button className="w-full sm:w-auto bg-slate-900 hover:bg-slate-800 text-white border border-slate-800 px-8 py-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 group">
                                <Play className="w-4 h-4 group-hover:text-indigo-400 transition-colors" />
                                Watch Demo
                            </button>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.5, delay: 0.5 }}
                            className="mt-12 flex items-center justify-center lg:justify-start gap-8 text-slate-500 text-sm font-medium"
                        >
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-indigo-500" />
                                <span>SOC2 Ready</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-indigo-500" />
                                <span>Open Source Core</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-indigo-500" />
                                <span>Usage-based Pricing</span>
                            </div>
                        </motion.div>
                    </div>

                    {/* 3D Tilt Visual */}
                    <div className="flex-1 w-full max-w-[600px] perspective-1000">
                        <TiltCard />
                    </div>
                </div>
            </div>
        </section>
    );
}

function TiltCard() {
    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const mouseX = useSpring(x, { stiffness: 500, damping: 100 });
    const mouseY = useSpring(y, { stiffness: 500, damping: 100 });

    function onMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
        const { left, top, width, height } = currentTarget.getBoundingClientRect();
        x.set((clientX - left - width / 2) / 25);
        y.set((clientY - top - height / 2) / 25);
    }

    return (
        <motion.div
            style={{ rotateX: mouseY, rotateY: mouseX }}
            onMouseMove={onMouseMove}
            onMouseLeave={() => {
                x.set(0);
                y.set(0);
            }}
            className="relative w-full aspect-square bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-2xl shadow-indigo-500/10 cursor-default transform-gpu transition-shadow hover:shadow-indigo-500/20"
        >
            {/* Floating Elements */}
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/50 to-transparent rounded-2xl pointer-events-none" />

            {/* Mock Interface */}
            <div className="relative h-full flex flex-col gap-4">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div className="flex gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
                        <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                        <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
                    </div>
                    <div className="h-2 w-20 bg-slate-800 rounded-full" />
                </div>

                {/* Canvas Area */}
                <div className="flex-1 relative bg-slate-950/50 rounded-lg border border-slate-800/50 overflow-hidden p-4">
                    <div className="absolute inset-0 bg-[radial-gradient(#312e81_1px,transparent_1px)] [background-size:16px_16px] opacity-20" />

                    {/* Nodes */}
                    <motion.div
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        className="absolute top-10 left-10 bg-slate-900 border border-indigo-500/50 p-3 rounded-lg shadow-lg w-40"
                    >
                        <div className="flex items-center gap-2 mb-2">
                            <Database className="w-4 h-4 text-indigo-400" />
                            <span className="text-xs font-semibold text-indigo-100">Postgres Source</span>
                        </div>
                        <div className="h-1 w-full bg-slate-800 rounded overflow-hidden">
                            <div className="h-full w-2/3 bg-indigo-500" />
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.7 }}
                        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-slate-900 border border-cyan-500/50 p-4 rounded-lg shadow-lg w-48 z-10"
                    >
                        <div className="flex items-center gap-2 mb-3">
                            <Brain className="w-5 h-5 text-cyan-400" />
                            <span className="text-sm font-semibold text-cyan-100">Reasoning Agent</span>
                        </div>
                        <div className="space-y-2">
                            <div className="h-2 w-full bg-slate-800 rounded animate-pulse" />
                            <div className="h-2 w-3/4 bg-slate-800 rounded animate-pulse" />
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ x: 20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.9 }}
                        className="absolute bottom-10 right-10 bg-slate-900 border border-green-500/50 p-3 rounded-lg shadow-lg w-40"
                    >
                        <div className="flex items-center gap-2 mb-2">
                            <Zap className="w-4 h-4 text-green-400" />
                            <span className="text-xs font-semibold text-green-100">Action Trigger</span>
                        </div>
                        <div className="flex justify-between text-[10px] text-slate-500">
                            <span>Status</span>
                            <span className="text-green-400">Active</span>
                        </div>
                    </motion.div>

                    {/* Connecting Lines (SVG) */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none">
                        <motion.path
                            initial={{ pathLength: 0 }}
                            animate={{ pathLength: 1 }}
                            transition={{ duration: 1.5, delay: 1 }}
                            d="M130 80 C 200 80, 200 200, 250 200"
                            fill="none"
                            stroke="url(#gradient1)"
                            strokeWidth="2"
                        />
                        <motion.path
                            initial={{ pathLength: 0 }}
                            animate={{ pathLength: 1 }}
                            transition={{ duration: 1.5, delay: 1.2 }}
                            d="M350 200 C 400 200, 400 320, 450 320"
                            fill="none"
                            stroke="url(#gradient2)"
                            strokeWidth="2"
                        />
                        <defs>
                            <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#6366f1" />
                                <stop offset="100%" stopColor="#06b6d4" />
                            </linearGradient>
                            <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#06b6d4" />
                                <stop offset="100%" stopColor="#22c55e" />
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
            </div>
        </motion.div>
    );
}
