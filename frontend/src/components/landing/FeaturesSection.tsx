import { motion } from 'framer-motion';

export function FeaturesSection() {

  const features = [
    {
      badge: 'Visual RAG Builder',
      title: 'Build RAG Pipelines in Minutes',
      description:
        'Drag, drop, connect. Build retrieval-augmented generation pipelines without writing code. See your data flow from ingestion to generation.',
      items: [
        'Smart document chunking strategies',
        'Embed with OpenAI, Cohere, or local models',
        'Store in Pinecone, Weaviate, Chroma, or FAISS',
        'Hybrid search with reranking',
        'Connect to any LLM for generation',
      ],
      reverse: false,
    },
    {
      badge: 'Full Observability',
      title: 'See Every Token, Every Cost',
      description:
        'Complete visibility into your AI workflows. Track costs, tokens, latency, and errors in real-time. Debug issues instantly with full execution traces.',
      items: [
        'Live execution progress with streaming',
        'Per-node cost tracking ($0.0012 per call)',
        'Token usage breakdown (input/output)',
        'Execution timeline and duration',
        'Detailed trace logs for debugging',
      ],
      reverse: true,
    },
    {
      badge: '52+ Nodes',
      title: 'Everything You Need, Pre-Built',
      description:
        'From LLMs to databases, OCR to email. Build any AI workflow with our comprehensive node library. New nodes added weekly.',
      items: [
        'LLM: OpenAI, Anthropic, Google, Azure',
        'Agents: CrewAI, LangChain multi-agent',
        'Processing: Chunk, OCR, Transcribe, NLP',
        'Storage: Vector DB, S3, Drive, PostgreSQL',
        'Integrations: Slack, Email, Reddit, Webhooks',
      ],
      reverse: false,
    },
  ];

  return (
    <section className="py-32 px-4 sm:px-6 lg:px-8 relative z-10">
      <div className="max-w-6xl mx-auto space-y-32">
        {features.map((feature, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '0px' }}
            transition={{ duration: 0.8, delay: index * 0.2 }}
            className={`grid grid-cols-1 lg:grid-cols-2 gap-16 items-center ${
              feature.reverse ? 'lg:flex-row-reverse' : ''
            }`}
          >
            <div className={feature.reverse ? 'lg:order-2' : ''}>
              <motion.div
                initial={{ opacity: 0, x: feature.reverse ? 40 : -40 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '0px' }}
                transition={{ duration: 0.8, delay: index * 0.2 + 0.1 }}
              >
                <span className="inline-flex px-4 py-1.5 bg-gradient-to-r from-pink-500/10 to-amber-500/10 border border-pink-500/30 rounded-full text-xs font-semibold text-pink-400 mb-5">
                  {feature.badge}
                </span>
                <h3 className="text-4xl font-black mb-5">{feature.title}</h3>
                <p className="text-lg text-slate-400 mb-8 leading-relaxed">{feature.description}</p>
                <ul className="space-y-4">
                  {feature.items.map((item, itemIndex) => (
                    <li key={itemIndex} className="flex items-center gap-4 text-slate-300">
                      <div className="w-6 h-6 rounded-full bg-green-500/15 flex items-center justify-center flex-shrink-0">
                        <span className="text-green-400 text-xs font-bold">✓</span>
                      </div>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            </div>
            <div className={feature.reverse ? 'lg:order-1' : ''}>
              <motion.div
                initial={{ opacity: 0, x: feature.reverse ? -40 : 40 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '0px' }}
                transition={{ duration: 0.8, delay: index * 0.2 + 0.1 }}
                className="aspect-[4/3] rounded-3xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 flex items-center justify-center relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-50" />
                <div className="text-center p-10 text-slate-500 text-sm relative z-10">
                  [Feature Visual Placeholder]
                </div>
              </motion.div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

