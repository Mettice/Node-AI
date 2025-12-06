import { Shield, Lock, FileKey, Eye, Server, Globe } from 'lucide-react';
import { motion } from 'framer-motion';

export function EnterpriseSpecs() {
    return (
        <section id="security" className="py-24 bg-slate-950 border-t border-slate-900 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                    <div>
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-3 py-1 mb-6"
                        >
                            <Shield className="w-4 h-4 text-indigo-400" />
                            <span className="text-xs font-medium text-indigo-300">Enterprise Grade Security</span>
                        </motion.div>

                        <motion.h2
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="text-3xl md:text-4xl font-bold text-white mb-6"
                        >
                            Security at the <br />
                            <span className="text-indigo-400">Infrastructure Level</span>
                        </motion.h2>

                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="text-lg text-slate-400 mb-8 leading-relaxed"
                        >
                            We don't just wrap APIs. We provide a secure execution environment for your most sensitive workflows.
                            SOC2 Type II ready architecture from day one.
                        </motion.p>

                        <div className="space-y-6">
                            <SpecItem
                                icon={Lock}
                                title="Encrypted Secrets Vault"
                                desc="API keys and credentials are encrypted at rest using AES-256 and never exposed to the client."
                                delay={0.3}
                            />
                            <SpecItem
                                icon={FileKey}
                                title="Private VPC Peering"
                                desc="Connect directly to your internal databases and services without exposing them to the public internet."
                                delay={0.4}
                            />
                            <SpecItem
                                icon={Eye}
                                title="Audit Logging"
                                desc="Every execution, edit, and access event is logged and exportable to your SIEM."
                                delay={0.5}
                            />
                        </div>
                    </div>

                    <div className="relative">
                        <div className="absolute inset-0 bg-indigo-500/20 blur-[100px] rounded-full"></div>
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            whileInView={{ scale: 1, opacity: 1 }}
                            transition={{ duration: 0.5 }}
                            className="relative bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl overflow-hidden"
                        >
                            {/* Scanline Effect */}
                            <div className="absolute inset-0 bg-[linear-gradient(transparent_0%,rgba(99,102,241,0.1)_50%,transparent_100%)] h-[200%] w-full animate-scanline pointer-events-none" />

                            <div className="flex items-center justify-between mb-8 border-b border-slate-800 pb-4">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                    <span className="text-sm font-mono text-slate-300">System Status: Operational</span>
                                </div>
                                <span className="text-xs text-slate-500 font-mono">ID: 8f92-a2b1</span>
                            </div>

                            <div className="space-y-4 font-mono text-xs">
                                <SpecRow label="Encryption Standard" value="AES-256-GCM" color="text-green-400" />
                                <SpecRow label="Data Residency" value="US-East (N. Virginia)" color="text-indigo-400" />
                                <SpecRow label="Compliance" value="SOC2, HIPAA, GDPR" color="text-indigo-400" />
                                <SpecRow label="Uptime (90d)" value="99.99%" color="text-green-400" />
                                <SpecRow label="Penetration Test" value="Passed (Q3 2024)" color="text-green-400" />
                            </div>

                            <div className="mt-8 pt-6 border-t border-slate-800 text-center">
                                <button className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors font-medium flex items-center justify-center gap-2 mx-auto">
                                    <Globe className="w-4 h-4" />
                                    Download Security Whitepaper
                                </button>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </div>
        </section>
    );
}

function SpecItem({ icon: Icon, title, desc, delay }: any) {
    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ delay }}
            className="flex gap-4 group"
        >
            <div className="mt-1 bg-slate-900 p-2 rounded-lg border border-slate-800 h-fit group-hover:border-indigo-500/50 transition-colors">
                <Icon className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
                <h3 className="text-white font-semibold mb-1 group-hover:text-indigo-300 transition-colors">{title}</h3>
                <p className="text-sm text-slate-400">{desc}</p>
            </div>
        </motion.div>
    );
}

function SpecRow({ label, value, color }: any) {
    return (
        <div className="flex justify-between items-center p-3 bg-slate-950 rounded border border-slate-800 hover:border-slate-700 transition-colors">
            <span className="text-slate-400">{label}</span>
            <span className={color}>{value}</span>
        </div>
    );
}
