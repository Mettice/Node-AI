import { motion } from 'framer-motion';

export function EnterpriseSection() {

  const features = [
    { icon: '🔐', title: 'SSO & RBAC', description: 'Single sign-on with SAML/OIDC. Role-based access for teams.' },
    { icon: '🔌', title: 'API & Webhooks', description: 'Trigger workflows via API or webhooks. Integrate anywhere.' },
    { icon: '📊', title: 'Audit Logs', description: 'Complete trail of every execution, change, and access.' },
    { icon: '🚀', title: 'One-Click Deploy', description: 'Deploy to production with versioning and rollback.' },
    { icon: '🔑', title: 'Secrets Vault', description: 'Secure vault for API keys. Environment-based config.' },
    { icon: '💰', title: 'Cost Controls', description: 'Per-workflow budgets. Alerts before overruns.' },
    { icon: '☁️', title: 'Self-Hosted', description: 'Deploy in your cloud. Keep data on your infrastructure.' },
    { icon: '🛡️', title: 'SOC 2', description: 'Enterprise-grade security. Regular pen testing.' },
  ];

  return (
    <section className="py-32 px-4 sm:px-6 lg:px-8 relative z-10">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '0px' }}
          transition={{ duration: 0.6 }}
          className="mb-16"
        >
          <div className="inline-flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-4 relative pl-6">
            <span className="absolute left-0 w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
            Enterprise Ready
          </div>
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-5">
            Built for Scale & Security
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl leading-relaxed">
            Deploy with confidence. NodeAI meets enterprise security and compliance needs.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '0px' }}
              transition={{ duration: 0.6, delay: 0.05 * index }}
              className="bg-slate-900/50 border border-slate-800 rounded-2xl p-7 hover:bg-slate-900/70 hover:border-cyan-500/30 hover:-translate-y-1 transition-all"
            >
              <div className="w-11 h-11 rounded-xl bg-cyan-500/10 flex items-center justify-center text-2xl mb-5">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

