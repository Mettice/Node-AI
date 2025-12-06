import { motion } from 'framer-motion';
import { useRef } from 'react';
import { useScroll, useTransform } from 'framer-motion';
import { Brain, Code, MessageSquare, Users } from 'lucide-react';

export function VisualMultiAgent() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  const rotate = useTransform(scrollYProgress, [0, 1], [0, 360]);
  const scale = useTransform(scrollYProgress, [0, 0.5, 1], [0.8, 1, 0.8]);

  return (
    <section ref={containerRef} className="py-32 bg-slate-950 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_theme(colors.purple.900/20),_transparent_70%)]" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center mb-20">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ margin: "-100px" }}
            className="text-5xl md:text-6xl font-bold text-white mb-6"
          >
            Multi-Agent <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">Orchestration</span>
          </motion.h2>
        </div>

        {/* 3D Agent Circle */}
        <div className="relative h-[600px] flex items-center justify-center">
          {/* Central Hub */}
          <motion.div
            style={{ scale }}
            className="absolute z-20 w-32 h-32 bg-gradient-to-br from-purple-500/20 to-cyan-500/20 border-2 border-purple-500/30 rounded-full flex items-center justify-center backdrop-blur-sm"
          >
            <Users className="w-16 h-16 text-purple-400" />
          </motion.div>

          {/* Orbiting Agents */}
          <motion.div
            style={{ rotate }}
            className="absolute inset-0"
          >
            <AgentOrbit
              angle={0}
              icon={Brain}
              label="Researcher"
              color="purple"
              delay={0}
            />
            <AgentOrbit
              angle={120}
              icon={Code}
              label="Coder"
              color="cyan"
              delay={0.2}
            />
            <AgentOrbit
              angle={240}
              icon={MessageSquare}
              label="Writer"
              color="indigo"
              delay={0.4}
            />
          </motion.div>

          {/* Connection Lines */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            <motion.line
              x1="50%"
              y1="50%"
              x2="50%"
              y2="20%"
              stroke="url(#agentGradient)"
              strokeWidth="2"
              initial={{ pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ margin: "-100px" }}
              transition={{ duration: 1, delay: 0.5 }}
            />
            <motion.line
              x1="50%"
              y1="50%"
              x2="25%"
              y2="75%"
              stroke="url(#agentGradient)"
              strokeWidth="2"
              initial={{ pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ margin: "-100px" }}
              transition={{ duration: 1, delay: 0.7 }}
            />
            <motion.line
              x1="50%"
              y1="50%"
              x2="75%"
              y2="75%"
              stroke="url(#agentGradient)"
              strokeWidth="2"
              initial={{ pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ margin: "-100px" }}
              transition={{ duration: 1, delay: 0.9 }}
            />
            <defs>
              <linearGradient id="agentGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#a855f7" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.5" />
              </linearGradient>
            </defs>
          </svg>

          {/* Floating Particles */}
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-purple-400/30 rounded-full"
              initial={{
                x: Math.random() * 800,
                y: Math.random() * 600,
                opacity: 0,
              }}
              animate={{
                x: Math.random() * 800,
                y: Math.random() * 600,
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: 3 + Math.random() * 2,
                repeat: Infinity,
                delay: Math.random() * 2,
              }}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

function AgentOrbit({ angle, icon: Icon, label, color, delay }: any) {
  const radius = 200;
  const centerX = 50; // percentage
  const centerY = 50; // percentage
  
  const x = centerX + (radius / 8) * Math.cos((angle * Math.PI) / 180);
  const y = centerY + (radius / 8) * Math.sin((angle * Math.PI) / 180);

  const colorClasses = {
    purple: "from-purple-500/20 to-purple-500/5 border-purple-500/30 text-purple-400",
    cyan: "from-cyan-500/20 to-cyan-500/5 border-cyan-500/30 text-cyan-400",
    indigo: "from-indigo-500/20 to-indigo-500/5 border-indigo-500/30 text-indigo-400",
  };

  const bgClass = colorClasses[color as keyof typeof colorClasses];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ margin: "-100px" }}
      transition={{ duration: 0.5, delay }}
      className="absolute"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        transform: 'translate(-50%, -50%)',
      }}
    >
      <motion.div
        whileHover={{ scale: 1.15, rotate: 5 }}
        className={`bg-gradient-to-br ${bgClass} border rounded-xl p-6 w-40 cursor-pointer backdrop-blur-sm shadow-lg`}
      >
        <div className="text-center">
          <motion.div
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 2, repeat: Infinity, delay }}
          >
            <Icon className={`w-10 h-10 mx-auto mb-2 ${color === 'purple' ? 'text-purple-400' : color === 'cyan' ? 'text-cyan-400' : 'text-indigo-400'}`} />
          </motion.div>
          <div className="text-sm font-bold text-white">{label}</div>
        </div>
      </motion.div>
    </motion.div>
  );
}

