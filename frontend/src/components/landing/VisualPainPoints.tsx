import { motion } from 'framer-motion';
import { useRef } from 'react';
import { useScroll, useTransform } from 'framer-motion';
import { Code, DollarSign, Eye, Zap, CheckCircle, Clock } from 'lucide-react';

export function VisualPainPoints() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

  const problems = [
    { icon: Code, color: "red", problem: "Weeks of Coding", solution: "Build in Hours" },
    { icon: DollarSign, color: "orange", problem: "Cost Spiral", solution: "30-60% Savings" },
    { icon: Eye, color: "yellow", problem: "Black Box", solution: "100% Visibility" },
    { icon: Zap, color: "purple", problem: "Complex Setup", solution: "Zero-Code" },
    { icon: CheckCircle, color: "blue", problem: "Hard to Test", solution: "Built-in QA" },
    { icon: Clock, color: "cyan", problem: "Slow Iteration", solution: "10x Faster" },
  ];

  return (
    <section ref={containerRef} className="py-32 bg-gradient-to-b from-slate-950 to-slate-900 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0">
        <motion.div
          className="absolute top-0 left-0 w-full h-full"
          animate={{
            background: [
              "radial-gradient(circle at 20% 50%, rgba(239, 68, 68, 0.1), transparent 50%)",
              "radial-gradient(circle at 80% 50%, rgba(239, 68, 68, 0.1), transparent 50%)",
              "radial-gradient(circle at 20% 50%, rgba(239, 68, 68, 0.1), transparent 50%)",
            ],
          }}
          transition={{ duration: 5, repeat: Infinity }}
        />
      </div>

      <motion.div
        style={{ opacity }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10"
      >
        <div className="text-center mb-20">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ margin: "-100px" }}
            className="text-5xl md:text-6xl font-bold text-white mb-6"
          >
            Stop <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-orange-400">Struggling</span>
          </motion.h2>
        </div>

        {/* Problem/Solution Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {problems.map((item, index) => (
            <ProblemCard key={index} item={item} index={index} />
          ))}
        </div>
      </motion.div>
    </section>
  );
}

function ProblemCard({ item, index }: any) {
  const Icon = item.icon;
  
  const colorClasses = {
    red: "from-red-500/20 to-red-500/5 border-red-500/30 text-red-400",
    orange: "from-orange-500/20 to-orange-500/5 border-orange-500/30 text-orange-400",
    yellow: "from-yellow-500/20 to-yellow-500/5 border-yellow-500/30 text-yellow-400",
    purple: "from-purple-500/20 to-purple-500/5 border-purple-500/30 text-purple-400",
    blue: "from-blue-500/20 to-blue-500/5 border-blue-500/30 text-blue-400",
    cyan: "from-cyan-500/20 to-cyan-500/5 border-cyan-500/30 text-cyan-400",
  };

  const bgClass = colorClasses[item.color as keyof typeof colorClasses];

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ margin: "-50px" }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="relative group"
    >
      {/* Problem Side */}
      <motion.div
        whileHover={{ rotateY: 180 }}
        className="relative h-64"
        style={{ transformStyle: 'preserve-3d', perspective: '1000px' }}
      >
        <div className={`absolute inset-0 bg-gradient-to-br ${bgClass} border rounded-2xl p-6 backdrop-blur-sm`} style={{ backfaceVisibility: 'hidden' }}>
          <div className="text-center h-full flex flex-col items-center justify-center">
            <motion.div
              animate={{ rotate: [0, -10, 10, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              {(() => {
                const iconColors = {
                  red: "text-red-400",
                  orange: "text-orange-400",
                  yellow: "text-yellow-400",
                  purple: "text-purple-400",
                  blue: "text-blue-400",
                  cyan: "text-cyan-400",
                };
                return <Icon className={`w-12 h-12 mx-auto mb-4 ${iconColors[item.color as keyof typeof iconColors]}`} />;
              })()}
            </motion.div>
            <div className="text-xl font-bold text-white mb-2">{item.problem}</div>
            <div className="text-sm text-slate-400">Problem</div>
          </div>
        </div>

        {/* Solution Side */}
        <div className={`absolute inset-0 bg-gradient-to-br from-green-500/20 to-green-500/5 border-green-500/30 border rounded-2xl p-6 backdrop-blur-sm`} style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}>
          <div className="text-center h-full flex flex-col items-center justify-center">
            <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-400" />
            <div className="text-xl font-bold text-white mb-2">{item.solution}</div>
            <div className="text-sm text-green-400">Solution</div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

