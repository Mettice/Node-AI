import { motion } from 'framer-motion';
import { FeatureVideo } from './FeatureVideo';

export function FeaturesSection() {

  const features = [
    {
      badge: 'Cost Intelligence',
      title: 'Cut AI Costs by 70%',
      description:
        'Stop overpaying for AI. Intelligent model routing sends simple queries to cheaper models, complex ones to GPT-4. Real-time cost tracking shows exactly where every dollar goes.',
      items: [
        'Automatic model routing by task complexity',
        'Per-token cost tracking across all providers',
        'Cost forecasting and budget alerts',
        'Compare GPT-4 vs Claude vs Gemini costs',
        'ROI dashboard for AI investments',
      ],
      reverse: false,
    },
    {
      badge: 'Production RAG',
      title: 'RAG Pipelines That Actually Work',
      description:
        'Build retrieval-augmented generation with vector databases, hybrid search, and reranking. Connect to Pinecone, FAISS, ChromaDB, or Weaviate in minutes.',
      items: [
        'Smart chunking with overlap control',
        'Embed with OpenAI, Cohere, or local models',
        'Hybrid search: semantic + keyword',
        'Reranking for precision retrieval',
        'Knowledge base management UI',
      ],
      reverse: true,
    },
    {
      badge: 'Multi-Agent Systems',
      title: 'CrewAI + LangChain Built-In',
      description:
        'Orchestrate AI agents that collaborate, delegate, and reason together. Visual Agent Rooms let you watch multi-agent conversations in real-time.',
      items: [
        'CrewAI integration with visual debugging',
        'LangChain agents and tools',
        'Agent memory and context sharing',
        'Watch agents think in real-time',
        'Custom tool integration (MCP support)',
      ],
      reverse: false,
    },
    {
      badge: 'Enterprise Observability',
      title: 'Full Trace Visibility',
      description:
        'LangSmith and Langfuse integration built-in. Track every LLM call, debug failures, and optimize performance with detailed traces.',
      items: [
        'Langfuse + LangSmith integration',
        'Per-node execution traces',
        'Token usage breakdown (input/output)',
        'Latency monitoring and alerts',
        'Export traces for compliance',
      ],
      reverse: true,
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
                className="aspect-[4/3] rounded-3xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 relative overflow-hidden"
              >
                {/* Video mapping: Cost Intelligence (0), RAG (1), Multi-Agent (2), Observability (3) */}
                {index === 0 && (
                  <FeatureVideo
                    videoSrc="/videos/observability.mp4"
                    fallbackSrc="/images/cost-intelligence-fallback.jpg"
                    alt="Cost Intelligence Dashboard"
                  />
                )}
                {index === 1 && (
                  <FeatureVideo
                    videoSrc="/videos/rag-pipeline.mp4"
                    fallbackSrc="/images/rag-pipeline-fallback.jpg"
                    alt="RAG Pipeline Flow"
                  />
                )}
                {index === 2 && (
                  <FeatureVideo
                    videoSrc="/videos/multi-agent.mp4"
                    fallbackSrc="/images/multi-agent-fallback.jpg"
                    alt="Multi-Agent Systems"
                  />
                )}
                {index === 3 && (
                  <FeatureVideo
                    videoSrc="/videos/observability.mp4"
                    fallbackSrc="/images/observability-fallback.jpg"
                    alt="Enterprise Observability"
                  />
                )}
              </motion.div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

