import { Users, Brain, Code, Workflow, Database, Eye, ArrowRight } from 'lucide-react';
import { motion, useMotionTemplate, useMotionValue } from 'framer-motion';

export function BentoGrid() {
    return (
        <section id="features" className="py-24 bg-slate-950 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
                        The Complete <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">GenAI Development Stack</span>
                    </h2>
                    <p className="text-slate-400 max-w-2xl mx-auto">
                        Everything you need to build, deploy, and monitor intelligent agents.
                        From prompt engineering to production observability.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Large Card - Multi-Agent */}
                    <BentoCard
                        className="md:col-span-2"
                        title="Multi-Agent Orchestration"
                        description="Build complex teams of agents that collaborate to solve problems. Define roles, goals, and tools visually."
                        icon={Users}
                        color="purple"
                    >
                        <div className="absolute bottom-0 right-0 w-3/4 h-3/4 bg-slate-900 rounded-tl-2xl border-t border-l border-slate-800 p-4 overflow-hidden">
                            <div className="flex gap-4 mb-4">
                                <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3 flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Brain className="w-4 h-4 text-purple-400" />
                                        <span className="text-xs font-semibold text-purple-200">Researcher</span>
                                    </div>
                                    <div className="h-1.5 bg-slate-800 rounded w-full mb-1" />
                                    <div className="h-1.5 bg-slate-800 rounded w-2/3" />
                                </div>
                                <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-lg p-3 flex-1 mt-8">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Code className="w-4 h-4 text-cyan-400" />
                                        <span className="text-xs font-semibold text-cyan-200">Coder</span>
                                    </div>
                                    <div className="h-1.5 bg-slate-800 rounded w-full mb-1" />
                                    <div className="h-1.5 bg-slate-800 rounded w-2/3" />
                                </div>
                            </div>
                        </div>
                    </BentoCard>

                    {/* Tall Card - Observability */}
                    <BentoCard
                        className="md:row-span-2"
                        title="Full Observability"
                        description="Trace every execution. Track costs, latency, and token usage in real-time."
                        icon={Eye}
                        color="green"
                    >
                        <div className="mt-8 space-y-3">
                            <div className="bg-slate-900/50 rounded p-3 border border-slate-800">
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-slate-400">LLM Latency</span>
                                    <span className="text-green-400">1.2s</span>
                                </div>
                                <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-green-500 w-[60%]" />
                                </div>
                            </div>
                            <div className="bg-slate-900/50 rounded p-3 border border-slate-800">
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-slate-400">Cost / Run</span>
                                    <span className="text-green-400">$0.004</span>
                                </div>
                                <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-green-500 w-[30%]" />
                                </div>
                            </div>
                            <div className="bg-slate-900/50 rounded p-3 border border-slate-800">
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-slate-400">Success Rate</span>
                                    <span className="text-green-400">99.8%</span>
                                </div>
                                <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-green-500 w-[98%]" />
                                </div>
                            </div>
                        </div>
                    </BentoCard>

                    {/* Regular Card - Visual Builder */}
                    <BentoCard
                        title="Visual Builder"
                        description="Drag-and-drop workflow editor. No spaghetti code."
                        icon={Workflow}
                        color="blue"
                    />

                    {/* Regular Card - Integrations */}
                    <BentoCard
                        title="50+ Integrations"
                        description="Connect to Postgres, Slack, GitHub, and more."
                        icon={Database}
                        color="orange"
                    />
                </div>
            </div>
        </section>
    );
}

function BentoCard({ className, title, description, icon: Icon, color, children }: any) {
    const mouseX = useMotionValue(0);
    const mouseY = useMotionValue(0);

    function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
        const { left, top } = currentTarget.getBoundingClientRect();
        mouseX.set(clientX - left);
        mouseY.set(clientY - top);
    }

    return (
        <div
            className={`group relative border border-slate-800 bg-slate-900/50 overflow-hidden rounded-xl p-8 hover:border-slate-700 transition-colors ${className}`}
            onMouseMove={handleMouseMove}
        >
            <motion.div
                className="pointer-events-none absolute -inset-px rounded-xl opacity-0 transition duration-300 group-hover:opacity-100"
                style={{
                    background: useMotionTemplate`
            radial-gradient(
              650px circle at ${mouseX}px ${mouseY}px,
              rgba(99, 102, 241, 0.15),
              transparent 80%
            )
          `,
                }}
            />

            <div className="relative z-10 h-full flex flex-col">
                <div className={`w-12 h-12 rounded-lg bg-${color}-500/10 border border-${color}-500/20 flex items-center justify-center mb-4`}>
                    <Icon className={`w-6 h-6 text-${color}-400`} />
                </div>

                <h3 className="text-xl font-bold text-white mb-2">{title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-4 flex-1">{description}</p>

                {children}
            </div>
        </div>
    );
}
