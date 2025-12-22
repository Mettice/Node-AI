import { motion } from 'framer-motion';

export function UseCasesSection() {

  const useCases = [
    {
      icon: '🔬',
      title: 'Research Automation',
      description: 'Deploy agent crews to research topics, analyze data, and produce comprehensive reports automatically.',
      nodes: ['Agent Room', 'Web Search', 'Report'],
    },
    {
      icon: '💬',
      title: 'RAG Chatbots',
      description: 'Build chatbots that answer from your documents with accurate, cited responses.',
      nodes: ['Vector Search', 'Rerank', 'Chat'],
    },
    {
      icon: '✍️',
      title: 'Content Generation',
      description: 'Generate blog posts, social content, and marketing copy with AI agents that research and write.',
      nodes: ['Agent Room', 'Chat', 'Email'],
    },
    {
      icon: '📊',
      title: 'Data Analysis',
      description: 'Extract insights from documents, spreadsheets, and databases using AI-powered analysis.',
      nodes: ['Data Loader', 'NLP', 'Vision'],
    },
    {
      icon: '🎧',
      title: 'Customer Support',
      description: 'Automate support with AI that understands your docs and escalates when needed.',
      nodes: ['Webhook', 'Knowledge', 'Slack'],
    },
    {
      icon: '🎯',
      title: 'Sales Intelligence',
      description: 'Enrich leads, analyze prospects, and generate personalized outreach at scale.',
      nodes: ['Data Loader', 'Agent', 'Email'],
    },
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
            Use Cases
          </div>
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-5">
            Built for Every AI Workflow
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl leading-relaxed">
            From research automation to customer support — see what teams are building.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {useCases.map((useCase, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '0px' }}
              transition={{ duration: 0.6, delay: 0.1 * index }}
              className="bg-slate-900/50 border border-slate-800 rounded-3xl p-9 hover:bg-slate-900/70 hover:border-amber-500/30 hover:-translate-y-2 transition-all duration-400 relative overflow-hidden group"
            >
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 to-pink-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500/15 to-pink-500/15 flex items-center justify-center text-4xl mb-6">
                  {useCase.icon}
                </div>
                <h3 className="text-2xl font-bold mb-3">{useCase.title}</h3>
                <p className="text-slate-400 mb-6 leading-relaxed">{useCase.description}</p>
                <div className="flex gap-2 flex-wrap">
                  {useCase.nodes.map((node, nodeIndex) => (
                    <span
                      key={nodeIndex}
                      className="px-3 py-1.5 bg-slate-800/50 rounded-full text-xs text-slate-400 group-hover:bg-amber-500/15 group-hover:text-amber-400 transition-colors"
                    >
                      {node}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

