import { motion } from 'framer-motion';

export function ProblemSection() {

  const problems = [
    {
      icon: '💸',
      title: 'AI Costs Out of Control',
      description: "GPT-4 bills spike unexpectedly. No visibility into which workflows cost what. Finance asks questions you can't answer.",
    },
    {
      icon: '🔧',
      title: 'RAG Takes Months to Build',
      description: 'Vector databases, chunking strategies, embeddings, reranking — stitching these takes weeks and senior engineers.',
    },
    {
      icon: '🤖',
      title: 'Multi-Agent Chaos',
      description: "CrewAI agents fail silently. You can't see why agents made decisions or debug their reasoning chain.",
    },
    {
      icon: '📊',
      title: 'No Production Observability',
      description: "LLM calls are black boxes. When something fails at 2am, you're grepping logs instead of fixing issues.",
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
            Enterprise AI Is Broken
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl leading-relaxed">
            Teams waste months on infrastructure. Costs spiral. Production breaks. There's a better way.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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

