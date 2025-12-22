import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import { Home } from 'lucide-react';

export function AgentRoomsSection() {
  const [activeIndex, setActiveIndex] = useState(2);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % 3);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const agents = [
    {
      icon: '🔍',
      name: 'Senior Researcher',
      status: 'Completed',
      content: 'Research the topic: artificial intelligence on small business productivity. Focus on current trends and key statistics...',
      isActive: activeIndex === 0,
    },
    {
      icon: '📊',
      name: 'Data Analyst',
      status: 'Completed',
      content: 'Analyzing research data to identify: 1) Key trends and patterns 2) Automation opportunities 3) ROI metrics...',
      isActive: activeIndex === 1,
    },
    {
      icon: '✍️',
      name: 'Technical Writer',
      status: 'Thinking...',
      content: 'Creating a comprehensive research report that includes: 1) Executive summary 2) Methodology 3) Key findings...',
      isActive: activeIndex === 2,
    },
  ];

  const flowNodes = [
    { icon: '🔍', label: 'Researcher', isActive: activeIndex === 0 },
    { icon: '📊', label: 'Analyst', isActive: activeIndex === 1 },
    { icon: '✍️', label: 'Writer', isActive: activeIndex === 2 },
  ];

  return (
    <section className="relative py-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
      {/* Background Glow */}
      <div className="absolute inset-0 w-[1200px] h-[1200px] rounded-full bg-gradient-radial from-pink-500/12 via-transparent to-transparent blur-[80px] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" />

      <div className="max-w-4xl mx-auto relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '0px' }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <div className="inline-flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-4">
            <span className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
            Introducing Agent Rooms
          </div>
          <h2 className="text-5xl md:text-6xl font-black mb-6">
            Watch Your Agents{' '}
            <span className="bg-gradient-to-r from-pink-400 to-amber-400 bg-clip-text text-transparent">
              Think
            </span>
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            The first visual environment where you see multi-agent conversations unfold in real-time.
            Drop agents into a room, define their roles, watch them collaborate.
          </p>
        </motion.div>

        {/* Agent Room Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: '0px' }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="relative"
        >
          <div className="relative bg-slate-900/80 backdrop-blur-xl rounded-3xl p-8 border border-slate-800 overflow-hidden">
            {/* Animated Border */}
            <div className="absolute inset-0 rounded-3xl p-[2px] bg-gradient-to-r from-pink-500 via-amber-500 to-cyan-500 opacity-50 animate-gradient-x" style={{ backgroundSize: '300% 300%' }}>
              <div className="w-full h-full bg-slate-900 rounded-3xl" />
            </div>

            <div className="relative z-10">
              {/* Header */}
              <div className="flex justify-between items-center mb-8 pb-6 border-b border-slate-800">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-pink-500/20 to-amber-500/20 flex items-center justify-center text-2xl shadow-lg shadow-pink-500/20">
                    <Home className="w-6 h-6 text-pink-400" />
                  </div>
                  <div>
                    <div className="text-xl font-bold">Research Crew</div>
                    <div className="text-sm text-slate-400">CrewAI • 3 Agents</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-full text-sm font-semibold">
                  <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                  Running
                </div>
              </div>

              {/* Agent Bubbles */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                {agents.map((agent, index) => (
                  <motion.div
                    key={index}
                    animate={{
                      scale: agent.isActive ? 1.02 : 1,
                      borderColor: agent.isActive ? 'rgba(59, 130, 246, 0.3)' : 'rgba(255, 255, 255, 0.08)',
                    }}
                    className={`bg-slate-800/50 border rounded-2xl p-5 transition-all ${
                      agent.isActive ? 'shadow-lg shadow-blue-500/20' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-9 h-9 rounded-xl bg-slate-700/50 flex items-center justify-center text-lg">
                        {agent.icon}
                      </div>
                      <div>
                        <div className="text-sm font-semibold">{agent.name}</div>
                        <div
                          className={`text-xs ${
                            agent.isActive ? 'text-blue-400' : 'text-slate-400'
                          }`}
                        >
                          {agent.status}
                        </div>
                      </div>
                    </div>
                    <div className="text-sm text-slate-300 line-clamp-3 leading-relaxed">
                      {agent.content}
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Flow Diagram */}
              <div className="flex justify-center items-center gap-6 mb-8">
                {flowNodes.map((node, index) => (
                  <div key={index} className="flex items-center gap-6">
                    <motion.div
                      animate={{
                        scale: node.isActive ? 1.1 : 1,
                        boxShadow: node.isActive
                          ? '0 0 30px rgba(59, 130, 246, 0.4)'
                          : 'none',
                      }}
                      className="flex flex-col items-center gap-2"
                    >
                      <div
                        className={`w-14 h-14 rounded-full border-2 flex items-center justify-center text-2xl transition-all ${
                          node.isActive
                            ? 'bg-blue-500/20 border-blue-500'
                            : 'bg-slate-800/50 border-slate-700'
                        }`}
                      >
                        {node.icon}
                      </div>
                      <div className="text-xs text-slate-400 font-medium">{node.label}</div>
                    </motion.div>
                    {index < flowNodes.length - 1 && (
                      <div className="text-slate-600 text-2xl">→</div>
                    )}
                  </div>
                ))}
              </div>

              {/* Progress Bar */}
              <div className="bg-slate-800/50 rounded-xl p-5">
                <div className="flex justify-between text-sm mb-3">
                  <span className="text-slate-300">Technical Writer working...</span>
                  <span className="text-amber-400 font-semibold">67%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: '67%' }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    className="h-full bg-gradient-to-r from-pink-500 to-amber-500 rounded-full relative"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                  </motion.div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

