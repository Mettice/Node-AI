import { motion } from 'framer-motion';

export function ProblemSection() {

  const problems = [
    {
      icon: '📦',
      title: 'Black Box AI',
      description: "Can't see inside LLM calls. Token costs surprise you. Debugging is pure guesswork.",
    },
    {
      icon: '🔧',
      title: 'Code-Heavy Setup',
      description: 'LangChain, vector DBs, embeddings — stitching these takes weeks and specialized engineers.',
    },
    {
      icon: '🤖',
      title: 'Rigid Agents',
      description: "Multi-agent orchestration means rigid wiring. You can't see the conversation or debug behavior.",
    },
  ];

  return (
    <section className="py-32 px-4 sm:px-6 lg:px-8 relative z-10">
      <div className="max-w-6xl mx-auto">
        <div className="mb-16">
          <div className="inline-flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-4 relative pl-6">
            <span className="absolute left-0 w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
            The Problem
          </div>
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-5 max-w-3xl">
            Building AI Systems Is Still Too Hard
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl leading-relaxed">
            Most teams struggle with complex code, opaque AI behavior, and fragmented tools.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {problems.map((problem, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '0px' }}
              transition={{ duration: 0.6, delay: 0.1 * index }}
              className="bg-slate-900/50 border border-slate-800 rounded-3xl p-9 hover:bg-slate-900/70 hover:border-red-500/30 hover:-translate-y-2 transition-all duration-400 relative overflow-hidden group"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-3xl mb-6">
                  {problem.icon}
                </div>
                <h3 className="text-xl font-bold mb-3">{problem.title}</h3>
                <p className="text-slate-400 leading-relaxed">{problem.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

