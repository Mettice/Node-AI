import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

export function CTASection() {

  return (
    <section className="py-40 px-4 sm:px-6 lg:px-8 relative z-10 overflow-hidden text-center">
      <div className="absolute inset-0 w-[1000px] h-[1000px] rounded-full bg-gradient-radial from-amber-500/15 via-transparent to-transparent blur-[80px] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
      <div className="max-w-3xl mx-auto relative z-10">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '0px' }}
          transition={{ duration: 0.6 }}
          className="text-4xl md:text-5xl lg:text-6xl font-black mb-5"
        >
          Ready to Build?
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '0px' }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-xl text-slate-400 mb-12 leading-relaxed"
        >
          Start building AI workflows today. No credit card required.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '0px' }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            to="/register"
            className="group relative px-8 py-4 bg-gradient-to-r from-amber-500 to-orange-600 text-slate-950 rounded-xl font-bold text-lg transition-all hover:scale-105 hover:shadow-2xl hover:shadow-amber-500/40 flex items-center gap-2 overflow-hidden"
          >
            <span className="relative z-10">Start Building Free →</span>
            <div className="absolute inset-0 bg-gradient-to-r from-amber-400 to-amber-500 opacity-0 group-hover:opacity-100 transition-opacity" />
          </Link>
          <button className="px-8 py-4 bg-transparent border border-slate-700 text-white rounded-xl font-semibold text-lg transition-all hover:bg-slate-800/50 hover:border-slate-600">
            Book a Demo
          </button>
        </motion.div>
      </div>
    </section>
  );
}

