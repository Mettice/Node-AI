import { motion } from 'framer-motion';

export function LogosSection() {
  const logos = [
    'TechCorp',
    'DataFlow',
    'AI Labs',
    'CloudScale',
    'Enterprise AI',
    'NextGen',
  ];

  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8 border-t border-b border-slate-800 relative z-10 overflow-hidden">
      <p className="text-center text-xs text-slate-500 uppercase tracking-widest mb-8">
        Trusted by AI teams worldwide
      </p>
      <div className="overflow-hidden">
        <div className="flex gap-20 animate-scroll">
          {[...logos, ...logos].map((logo, index) => (
            <span
              key={index}
              className="text-xl font-bold text-slate-500 whitespace-nowrap hover:text-slate-400 transition-colors"
            >
              {logo}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

