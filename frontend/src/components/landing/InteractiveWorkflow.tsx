import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Database, Cpu, Globe, Zap, ArrowRight } from 'lucide-react';

export function InteractiveWorkflow() {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start end", "end start"]
    });

    const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);
    const scale = useTransform(scrollYProgress, [0, 0.2], [0.8, 1]);

    const steps = [
        {
            id: 1,
            title: "Connect Data",
            description: "Securely connect to your existing databases and APIs. We support Postgres, Mongo, REST, and GraphQL out of the box.",
            icon: Database,
            color: "blue"
        },
        {
            id: 2,
            title: "Build Agents",
            description: "Drag and drop specialized agents. Configure their roles, tools, and goals using our visual builder.",
            icon: Cpu,
            color: "purple"
        },
        {
            id: 3,
            title: "Deploy & Scale",
            description: "One-click deployment to a serverless edge network. Auto-scaling, load balancing, and global distribution included.",
            icon: Globe,
            color: "green"
        }
    ];

    return (
        <section ref={containerRef} className="py-32 bg-slate-950 relative overflow-hidden">
            {/* Background Elements */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_theme(colors.indigo.900/10),_transparent_70%)]" />

            <motion.div
                style={{ opacity, scale }}
                className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10"
            >
                <div className="text-center mb-24">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                        className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 mb-6"
                    >
                        <Zap className="w-4 h-4 text-indigo-400" />
                        <span className="text-sm font-medium text-indigo-300">Workflow Engine</span>
                    </motion.div>

                    <motion.h2
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.1 }}
                        className="text-4xl md:text-5xl font-bold text-white mb-6"
                    >
                        From Idea to Production <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">In Three Steps</span>
                    </motion.h2>
                </div>

                <div className="relative">
                    {/* Connecting Line */}
                    <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-slate-800 -translate-x-1/2 hidden md:block" />

                    <div className="space-y-24">
                        {steps.map((step, index) => (
                            <WorkflowStep key={step.id} step={step} index={index} />
                        ))}
                    </div>
                </div>
            </motion.div>
        </section>
    );
}

function WorkflowStep({ step, index }: { step: any, index: number }) {
    const isEven = index % 2 === 0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ margin: "-100px" }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className={`flex flex-col md:flex-row items-center gap-8 md:gap-16 ${isEven ? '' : 'md:flex-row-reverse'}`}
        >
            {/* Text Content */}
            <div className={`flex-1 text-center ${isEven ? 'md:text-right' : 'md:text-left'}`}>
                <div className={`inline-flex p-3 rounded-xl bg-${step.color}-500/10 border border-${step.color}-500/20 mb-4`}>
                    <step.icon className={`w-6 h-6 text-${step.color}-400`} />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">{step.title}</h3>
                <p className="text-slate-400 leading-relaxed max-w-md mx-auto md:mx-0 ml-auto">
                    {step.description}
                </p>
            </div>

            {/* Center Node (Desktop) */}
            <div className="relative hidden md:flex items-center justify-center w-12 h-12 shrink-0">
                <div className={`w-4 h-4 rounded-full bg-${step.color}-500 ring-4 ring-slate-950 relative z-10`} />
                <div className={`absolute inset-0 bg-${step.color}-500/50 blur-xl rounded-full`} />
            </div>

            {/* Visual Content */}
            <div className="flex-1 w-full">
                <div className="relative group">
                    <div className={`absolute inset-0 bg-${step.color}-500/10 blur-2xl rounded-xl transition-opacity opacity-50 group-hover:opacity-100`} />
                    <div className="relative bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-colors">
                        {/* Mock UI based on step */}
                        {step.id === 1 && (
                            <div className="space-y-3 font-mono text-xs">
                                <div className="flex items-center justify-between text-slate-500">
                                    <span>source</span>
                                    <span>status</span>
                                </div>
                                <div className="flex items-center justify-between p-2 bg-slate-950 rounded border border-slate-800">
                                    <div className="flex items-center gap-2">
                                        <Database className="w-3 h-3 text-blue-400" />
                                        <span className="text-slate-300">Production DB</span>
                                    </div>
                                    <span className="text-green-400">Connected</span>
                                </div>
                                <div className="flex items-center justify-between p-2 bg-slate-950 rounded border border-slate-800">
                                    <div className="flex items-center gap-2">
                                        <Globe className="w-3 h-3 text-amber-400" />
                                        <span className="text-slate-300">Stripe API</span>
                                    </div>
                                    <span className="text-green-400">Connected</span>
                                </div>
                            </div>
                        )}

                        {step.id === 2 && (
                            <div className="space-y-3">
                                <div className="flex gap-2">
                                    <div className="w-8 h-8 rounded bg-amber-500/20 flex items-center justify-center border border-amber-500/30">
                                        <Cpu className="w-4 h-4 text-amber-400" />
                                    </div>
                                    <div className="flex-1">
                                        <div className="h-2 w-24 bg-slate-800 rounded mb-2" />
                                        <div className="h-2 w-16 bg-slate-800 rounded" />
                                    </div>
                                </div>
                                <div className="pl-4 border-l border-slate-800 ml-4 space-y-2">
                                    <div className="flex items-center gap-2 text-xs text-slate-400">
                                        <ArrowRight className="w-3 h-3" />
                                        <span>Process Data</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-slate-400">
                                        <ArrowRight className="w-3 h-3" />
                                        <span>Generate Report</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {step.id === 3 && (
                            <div className="space-y-2">
                                <div className="flex items-center justify-between text-xs mb-4">
                                    <span className="text-slate-400">Deployment Status</span>
                                    <span className="text-green-400 flex items-center gap-1">
                                        <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                                        Live
                                    </span>
                                </div>
                                <div className="grid grid-cols-3 gap-2">
                                    <div className="bg-slate-950 p-2 rounded border border-slate-800 text-center">
                                        <div className="text-xs text-slate-500">US-East</div>
                                        <div className="text-green-400 text-xs">●</div>
                                    </div>
                                    <div className="bg-slate-950 p-2 rounded border border-slate-800 text-center">
                                        <div className="text-xs text-slate-500">EU-West</div>
                                        <div className="text-green-400 text-xs">●</div>
                                    </div>
                                    <div className="bg-slate-950 p-2 rounded border border-slate-800 text-center">
                                        <div className="text-xs text-slate-500">Asia-Pac</div>
                                        <div className="text-green-400 text-xs">●</div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
