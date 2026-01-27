import { Check, X, Minus } from 'lucide-react';
import { motion } from 'framer-motion';

export function ComparisonSection() {
    const features = [
        { name: "Visual RAG Pipeline Builder", nodeai: true, inhouse: "Weeks", competitor: "Code-only" },
        { name: "Multi-Agent (CrewAI + LangChain)", nodeai: true, inhouse: "Hard", competitor: "Limited" },
        { name: "Per-Token Cost Tracking", nodeai: true, inhouse: false, competitor: false },
        { name: "Intelligent Model Routing", nodeai: true, inhouse: false, competitor: false },
        { name: "Langfuse + LangSmith Integration", nodeai: true, inhouse: "Custom", competitor: "Manual" },
        { name: "Vector DB (Pinecone, FAISS, Chroma)", nodeai: true, inhouse: "Custom", competitor: true },
        { name: "Agent Room Visualization", nodeai: true, inhouse: false, competitor: false },
        { name: "Enterprise SSO & RBAC", nodeai: true, inhouse: "Custom", competitor: "Enterprise Plan" },
        { name: "Audit Logs (SIEM)", nodeai: true, inhouse: "Custom", competitor: "Enterprise Plan" },
    ];

    return (
        <section className="py-24 bg-slate-950 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
                        Why Engineering Teams <br />
                        <span className="text-indigo-400">Choose NodeAI</span>
                    </h2>
                    <p className="text-slate-400 max-w-2xl mx-auto">
                        Cut AI costs by 70%. Ship RAG pipelines in days, not months.
                        Stop rebuilding what we've already solved.
                    </p>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                        <thead>
                            <tr>
                                <th className="p-4 text-left text-slate-400 font-medium border-b border-slate-800 w-1/3">Feature</th>
                                <th className="p-4 text-center text-white font-bold border-b border-indigo-500/50 bg-indigo-500/10 rounded-t-xl w-1/4">
                                    <div className="flex flex-col items-center gap-1">
                                        <span className="text-lg">NodeAI</span>
                                        <span className="text-xs font-normal text-indigo-300">Production Platform</span>
                                    </div>
                                </th>
                                <th className="p-4 text-center text-slate-400 font-medium border-b border-slate-800 w-1/4">In-House Build</th>
                                <th className="p-4 text-center text-slate-400 font-medium border-b border-slate-800 w-1/4">Legacy iPaaS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {features.map((feature, index) => (
                                <motion.tr
                                    key={index}
                                    initial={{ opacity: 0, y: 10 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    className="group hover:bg-slate-900/30 transition-colors"
                                >
                                    <td className="p-4 text-slate-300 border-b border-slate-800 font-medium">{feature.name}</td>

                                    {/* NodeAI Column */}
                                    <td className="p-4 text-center border-b border-slate-800 bg-indigo-500/5 group-hover:bg-indigo-500/10 transition-colors border-x border-indigo-500/10">
                                        <div className="flex justify-center">
                                            <div className="w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center">
                                                <Check className="w-4 h-4 text-green-400" />
                                            </div>
                                        </div>
                                    </td>

                                    {/* In-House Column */}
                                    <td className="p-4 text-center border-b border-slate-800 text-slate-500">
                                        {feature.inhouse === true ? (
                                            <div className="flex justify-center"><Check className="w-4 h-4 text-slate-400" /></div>
                                        ) : feature.inhouse === false ? (
                                            <div className="flex justify-center"><X className="w-4 h-4 text-slate-600" /></div>
                                        ) : (
                                            <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">{feature.inhouse}</span>
                                        )}
                                    </td>

                                    {/* Competitor Column */}
                                    <td className="p-4 text-center border-b border-slate-800 text-slate-500">
                                        {feature.competitor === true ? (
                                            <div className="flex justify-center"><Check className="w-4 h-4 text-slate-400" /></div>
                                        ) : feature.competitor === false ? (
                                            <div className="flex justify-center"><X className="w-4 h-4 text-slate-600" /></div>
                                        ) : (
                                            <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">{feature.competitor}</span>
                                        )}
                                    </td>
                                </motion.tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    );
}
