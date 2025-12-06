import { motion } from 'framer-motion';
import { useRef } from 'react';
import { useScroll, useTransform } from 'framer-motion';

export function VisualGenAIStack() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.2], [0.9, 1]);

  return (
    <section ref={containerRef} className="py-32 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <motion.div
        style={{ opacity, scale }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10"
      >
        <div className="text-center mb-20">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ margin: "-100px" }}
            className="text-5xl md:text-6xl font-bold text-white mb-6"
          >
            The Complete <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-400 to-green-400">GenAI Stack</span>
          </motion.h2>
        </div>

        {/* Visual Flow Canvas */}
        <div className="relative h-[600px] md:h-[800px]">
          {/* Animated Flow Path */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid meet">
            <defs>
              <linearGradient id="flowGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#6366f1" />
                <stop offset="25%" stopColor="#8b5cf6" />
                <stop offset="50%" stopColor="#06b6d4" />
                <stop offset="75%" stopColor="#10b981" />
                <stop offset="100%" stopColor="#f59e0b" />
              </linearGradient>
            </defs>
            
            {/* Animated Path */}
            <motion.path
              d="M 100 400 Q 300 200, 500 300 T 900 400 T 1100 400"
              fill="none"
              stroke="url(#flowGradient)"
              strokeWidth="4"
              initial={{ pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ margin: "-100px" }}
              transition={{ duration: 2, ease: "easeInOut" }}
              style={{ filter: 'drop-shadow(0 0 8px rgba(99, 102, 241, 0.5))' }}
            />
          </svg>

          {/* Floating Nodes */}
          <FlowNode
            x={100}
            y={400}
            delay={0}
            icon="📥"
            label="Data"
            color="blue"
            description="Files, APIs, Databases"
          />
          <FlowNode
            x={500}
            y={300}
            delay={0.3}
            icon="⚡"
            label="Process"
            color="purple"
            description="Chunk, Embed, Transform"
          />
          <FlowNode
            x={700}
            y={350}
            delay={0.6}
            icon="🗄️"
            label="Store"
            color="cyan"
            description="Vector DB, Knowledge Base"
          />
          <FlowNode
            x={900}
            y={400}
            delay={0.9}
            icon="🔍"
            label="Retrieve"
            color="green"
            description="Search, Rerank, Hybrid"
          />
          <FlowNode
            x={1100}
            y={400}
            delay={1.2}
            icon="🤖"
            label="Generate"
            color="orange"
            description="LLM, Agents, Multi-Agent"
          />
        </div>
      </motion.div>
    </section>
  );
}

function FlowNode({ x, y, delay, icon, label, color, description }: any) {
  const colorClasses = {
    blue: "from-blue-500/20 to-blue-500/5 border-blue-500/30",
    purple: "from-purple-500/20 to-purple-500/5 border-purple-500/30",
    cyan: "from-cyan-500/20 to-cyan-500/5 border-cyan-500/30",
    green: "from-green-500/20 to-green-500/5 border-green-500/30",
    orange: "from-orange-500/20 to-orange-500/5 border-orange-500/30",
  };

  const bgClass = colorClasses[color as keyof typeof colorClasses];

  const glowColors = {
    blue: "bg-blue-500/20",
    purple: "bg-purple-500/20",
    cyan: "bg-cyan-500/20",
    green: "bg-green-500/20",
    orange: "bg-orange-500/20",
  };
  const glowClass = glowColors[color as keyof typeof glowColors];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ margin: "-100px" }}
      transition={{ duration: 0.5, delay }}
      className="absolute"
      style={{
        left: `${(x / 1200) * 100}%`,
        top: `${(y / 800) * 100}%`,
        transform: 'translate(-50%, -50%)',
      }}
    >
      <motion.div
        whileHover={{ scale: 1.1 }}
        className={`relative bg-gradient-to-br ${bgClass} border rounded-2xl p-6 w-48 cursor-pointer backdrop-blur-sm group`}
      >
        {/* Glow Effect */}
        <div className={`absolute inset-0 ${glowClass} rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity`} />
        
        <div className="relative z-10 text-center">
          <div className="text-4xl mb-2">{icon}</div>
          <div className="text-lg font-bold text-white mb-1">{label}</div>
          <div className="text-xs text-slate-400">{description}</div>
        </div>

        {/* Animated Particles */}
        <motion.div
          className="absolute inset-0 overflow-hidden rounded-2xl"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ margin: "-100px" }}
        >
          {[...Array(5)].map((_, i) => {
            const particleColors = {
              blue: "bg-blue-400",
              purple: "bg-purple-400",
              cyan: "bg-cyan-400",
              green: "bg-green-400",
              orange: "bg-orange-400",
            };
            const particleClass = particleColors[color as keyof typeof particleColors];
            return (
              <motion.div
                key={i}
                className={`absolute w-1 h-1 ${particleClass} rounded-full`}
                initial={{
                  x: Math.random() * 200 - 100,
                  y: Math.random() * 200 - 100,
                  opacity: 0,
                }}
                animate={{
                  x: Math.random() * 200 - 100,
                  y: Math.random() * 200 - 100,
                  opacity: [0, 1, 0],
                }}
                transition={{
                  duration: 2 + Math.random(),
                  repeat: Infinity,
                  delay: Math.random() * 2,
                }}
              />
            );
          })}
        </motion.div>
      </motion.div>
    </motion.div>
  );
}

