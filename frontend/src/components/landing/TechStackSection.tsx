import { motion } from 'framer-motion';
import * as simpleIcons from 'simple-icons';

export function TechStackSection() {

  // Helper function to safely get icon or fallback
  const getIcon = (iconName: string, fallback: string = 'M12 2L12 22', fallbackColor: string = '6B7280') => {
    try {
      const icon = (simpleIcons as any)[iconName];
      if (icon && icon.path && icon.hex) {
        return { path: icon.path, hex: icon.hex, color: `#${icon.hex}` };
      }
      return { path: fallback, hex: fallbackColor, color: `#${fallbackColor}` };
    } catch {
      return { path: fallback, hex: fallbackColor, color: `#${fallbackColor}` };
    }
  };
  
  const integrations = [
    { name: 'OpenAI', icon: getIcon('siOpenai'), color: '#412991' },
    { name: 'Anthropic', icon: getIcon('siAnthropic', 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z'), color: '#D97706' },
    { name: 'Google AI', icon: getIcon('siGoogle'), color: '#4285F4' },
    { name: 'Azure', icon: getIcon('siMicrosoft', 'M1 1h10v10H1V1zm12 0h10v10H13V1zM1 13h10v10H1V13zm12 0h10v10H13V13z'), color: '#0078D4' },
    { name: 'Pinecone', icon: getIcon('siPinecone', 'M12 2l8 14H4l8-14z'), color: '#000000' },
    { name: 'LangChain', icon: getIcon('siLangchain', 'M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z'), color: '#1C3C3C' },
    { name: 'CrewAI', icon: getIcon('siCrewai', 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z', 'FF6B35'), color: undefined }, // Use icon.color from simple-icons
    { name: 'Slack', icon: getIcon('siSlack'), color: '#4A154B' },
    { name: 'Email', icon: getIcon('siGmail', 'M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-.887.651-1.636 1.636-1.636h.273L12 10.91l10.091-7.09h.273c.904 0 1.636.732 1.636 1.636z'), color: '#EA4335' },
    { name: 'AWS S3', icon: getIcon('siAmazonwebservices', 'M13.23 10.56V16L8 13.78 13.23 10.56M2.28 5.58L8 2V8.22L2.28 5.58M21.72 5.58L16 8.22V2L21.72 5.58M8 15.78V22L2.28 18.42L8 15.78M16 15.78L21.72 18.42L16 22V15.78M8.12 13.78L13.23 16L8.12 13.78'), color: '#FF9900' },
    { name: 'Google Drive', icon: getIcon('siGoogledrive'), color: '#4285F4' },
    { name: 'PostgreSQL', icon: getIcon('siPostgresql'), color: '#4169E1' },
  ];

  const allTechs = integrations;

  // Duplicate the array for seamless infinite scroll
  const duplicatedTechs = [...allTechs, ...allTechs];

  const TechIcon = ({ tech, index }: { tech: any; index: number }) => (
    <motion.div
      key={`${tech.name}-${index}`}
      className="flex-shrink-0 bg-slate-900/50 border border-slate-800 rounded-2xl p-6 flex flex-col items-center gap-3 hover:bg-slate-900/70 hover:border-slate-700 hover:-translate-y-1 transition-all cursor-pointer group min-w-[140px]"
      whileHover={{ scale: 1.05 }}
      transition={{ duration: 0.2 }}
    >
      <div 
        className="w-12 h-12 group-hover:scale-110 transition-transform flex items-center justify-center"
        style={{ color: tech.color || tech.icon.color }}
      >
        {tech.icon?.path ? (
          <svg 
            viewBox="0 0 24 24" 
            className="w-full h-full"
            fill="currentColor"
          >
            <path d={tech.icon.path} />
          </svg>
        ) : (
          <div className="w-full h-full bg-slate-600 rounded-lg flex items-center justify-center text-xs font-bold text-white">
            {tech.name.substring(0, 2).toUpperCase()}
          </div>
        )}
      </div>
      <div className="text-sm font-medium text-slate-300 text-center leading-tight">
        {tech.name}
      </div>
    </motion.div>
  );

  return (
    <section className="py-32 px-4 sm:px-6 lg:px-8 relative z-10 bg-gradient-to-b from-transparent via-slate-900/20 to-transparent border-t border-b border-slate-800 overflow-hidden">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '0px' }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-4 relative pl-6">
            <span className="absolute left-0 w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
            Integrations
          </div>
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-5">
            Connect Your Entire Stack
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Native integrations with the tools you already use. More added every week.
          </p>
        </motion.div>

        {/* Horizontal Scrolling Container */}
        <div className="relative">
          {/* Gradient masks for smooth scroll effect */}
          <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-slate-950 to-transparent z-10 pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-slate-950 to-transparent z-10 pointer-events-none" />
          
          {/* Scrolling animation container */}
          <motion.div
            className="flex gap-4"
            animate={{
              x: [0, -2240] // Adjust based on total width of items
            }}
            transition={{
              x: {
                repeat: Infinity,
                repeatType: "loop",
                duration: 30,
                ease: "linear",
              },
            }}
          >
            {duplicatedTechs.map((tech, index) => (
              <TechIcon key={`tech-${index}`} tech={tech} index={index} />
            ))}
          </motion.div>
        </div>

      </div>
    </section>
  );
}