import { Shield, Lock, FileKey, Eye } from 'lucide-react';

export function TrustSection() {
    return (
        <section id="security" className="py-24 bg-slate-950 border-t border-slate-900 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                    <div>
                        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-3 py-1 mb-6">
                            <Shield className="w-4 h-4 text-indigo-400" />
                            <span className="text-xs font-medium text-indigo-300">Enterprise Grade</span>
                        </div>

                        <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
                            Security at the <br />
                            <span className="text-indigo-400">Infrastructure Level</span>
                        </h2>

                        <p className="text-lg text-slate-400 mb-8 leading-relaxed">
                            We don't just wrap APIs. We provide a secure execution environment for your most sensitive workflows.
                            SOC2 Type II ready architecture from day one.
                        </p>

                        <div className="space-y-6">
                            <div className="flex gap-4">
                                <div className="mt-1 bg-slate-900 p-2 rounded-lg border border-slate-800 h-fit">
                                    <Lock className="w-5 h-5 text-indigo-400" />
                                </div>
                                <div>
                                    <h3 className="text-white font-semibold mb-1">Encrypted Secrets Vault</h3>
                                    <p className="text-sm text-slate-400">API keys and credentials are encrypted at rest using AES-256 and never exposed to the client.</p>
                                </div>
                            </div>

                            <div className="flex gap-4">
                                <div className="mt-1 bg-slate-900 p-2 rounded-lg border border-slate-800 h-fit">
                                    <FileKey className="w-5 h-5 text-indigo-400" />
                                </div>
                                <div>
                                    <h3 className="text-white font-semibold mb-1">Private VPC Peering</h3>
                                    <p className="text-sm text-slate-400">Connect directly to your internal databases and services without exposing them to the public internet.</p>
                                </div>
                            </div>

                            <div className="flex gap-4">
                                <div className="mt-1 bg-slate-900 p-2 rounded-lg border border-slate-800 h-fit">
                                    <Eye className="w-5 h-5 text-indigo-400" />
                                </div>
                                <div>
                                    <h3 className="text-white font-semibold mb-1">Audit Logging</h3>
                                    <p className="text-sm text-slate-400">Every execution, edit, and access event is logged and exportable to your SIEM.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="relative">
                        <div className="absolute inset-0 bg-indigo-500/20 blur-[100px] rounded-full"></div>
                        <div className="relative bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl">
                            <div className="flex items-center justify-between mb-8 border-b border-slate-800 pb-4">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                    <span className="text-sm font-mono text-slate-300">System Status: Operational</span>
                                </div>
                                <span className="text-xs text-slate-500 font-mono">ID: 8f92-a2b1</span>
                            </div>

                            <div className="space-y-4 font-mono text-xs">
                                <div className="flex justify-between items-center p-3 bg-slate-950 rounded border border-slate-800">
                                    <span className="text-slate-400">Encryption Standard</span>
                                    <span className="text-green-400">AES-256-GCM</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-slate-950 rounded border border-slate-800">
                                    <span className="text-slate-400">Data Residency</span>
                                    <span className="text-indigo-400">US-East (N. Virginia)</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-slate-950 rounded border border-slate-800">
                                    <span className="text-slate-400">Compliance</span>
                                    <span className="text-indigo-400">SOC2, HIPAA, GDPR</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-slate-950 rounded border border-slate-800">
                                    <span className="text-slate-400">Uptime (90d)</span>
                                    <span className="text-green-400">99.99%</span>
                                </div>
                            </div>

                            <div className="mt-8 pt-6 border-t border-slate-800 text-center">
                                <button className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors font-medium">
                                    Download Security Whitepaper →
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
