import { motion } from 'framer-motion';
import * as simpleIcons from 'simple-icons';

export function IntegrationsSection() {

  // Get CrewAI icon from simple-icons
  const getCrewAIIcon = () => {
    try {
      const icon = (simpleIcons as any).siCrewai;
      if (icon && icon.path && icon.hex) {
        return { path: icon.path, color: `#${icon.hex}` };
      }
    } catch {
      // Fallback if icon not found
    }
    return { path: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z', color: '#FF6B35' };
  };

  const crewAIIcon = getCrewAIIcon();

  const integrations = [
    { icon: '🤖', name: 'OpenAI', type: 'emoji' },
    { icon: '🧠', name: 'Anthropic', type: 'emoji' },
    { icon: '🔷', name: 'Google AI', type: 'emoji' },
    { icon: '☁️', name: 'Azure', type: 'emoji' },
    { icon: '🌲', name: 'Pinecone', type: 'emoji' },
    { icon: '🔗', name: 'LangChain', type: 'emoji' },
    { icon: crewAIIcon, name: 'CrewAI', type: 'svg' },
    { icon: '💬', name: 'Slack', type: 'emoji' },
    { icon: '📧', name: 'Email', type: 'emoji' },
    { icon: '🪣', name: 'AWS S3', type: 'emoji' },
    { icon: '📁', name: 'Google Drive', type: 'emoji' },
    { icon: '🗄️', name: 'PostgreSQL', type: 'emoji' },
  ];

  return (
    <section className="py-32 px-4 sm:px-6 lg:px-8 relative z-10 bg-gradient-to-b from-transparent via-slate-900/20 to-transparent border-t border-b border-slate-800">
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

        <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {integrations.map((integration, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true, margin: '0px' }}
              transition={{ duration: 0.4, delay: 0.05 * index }}
              className="bg-slate-900/50 border border-slate-800 rounded-2xl p-7 flex flex-col items-center gap-4 hover:bg-slate-900/70 hover:border-slate-700 hover:-translate-y-1 transition-all cursor-pointer group"
            >
              <div className="text-4xl group-hover:scale-125 transition-transform flex items-center justify-center">
                {integration.type === 'svg' ? (
                  <svg
                    viewBox="0 0 24 24"
                    className="w-10 h-10"
                    fill="currentColor"
                    style={{ color: (integration.icon as any).color }}
                  >
                    <path d={(integration.icon as any).path} />
                  </svg>
                ) : (
                  integration.icon as string
                )}
              </div>
              <div className="text-sm font-medium text-slate-300">{integration.name}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

