import { Building2, Heart, ShoppingCart, Scale, GraduationCap, Factory } from 'lucide-react';

export function IndustriesSection() {
  const industries = [
    {
      name: 'FinTech',
      icon: Building2,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/30',
      useCases: [
        'Loan processing automation',
        'KYC document verification',
        'Trading signal analysis',
        'Fraud detection workflows',
      ],
    },
    {
      name: 'Healthcare',
      icon: Heart,
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/30',
      useCases: [
        'Medical imaging analysis',
        'Clinical note processing',
        'Drug interaction detection',
        'Patient data analysis',
      ],
    },
    {
      name: 'E-commerce',
      icon: ShoppingCart,
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/30',
      useCases: [
        'Personalized recommendations',
        'Inventory optimization',
        'Visual product search',
        'Customer support automation',
      ],
    },
    {
      name: 'Legal',
      icon: Scale,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/30',
      useCases: [
        'Contract clause extraction',
        'Legal document analysis',
        'Case research automation',
        'Compliance monitoring',
      ],
    },
    {
      name: 'Education',
      icon: GraduationCap,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/10',
      borderColor: 'border-yellow-500/30',
      useCases: [
        'Automated grading',
        'Personalized learning paths',
        'Research assistance',
        'Content generation',
      ],
    },
    {
      name: 'Manufacturing',
      icon: Factory,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/10',
      borderColor: 'border-cyan-500/30',
      useCases: [
        'Quality control automation',
        'Predictive maintenance',
        'Supply chain optimization',
        'Document processing',
      ],
    },
  ];

  return (
    <section id="industries" className="py-24 bg-slate-950 border-t border-slate-900 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-3 py-1 mb-6">
            <span className="text-xs font-medium text-indigo-300">Industry Solutions</span>
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
            Powering AI Across <span className="text-indigo-400">Every Industry</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            From healthcare to finance, our platform adapts to your industry's unique needs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {industries.map((industry) => {
            const Icon = industry.icon;
            return (
              <div
                key={industry.name}
                className={`rounded-xl border ${industry.borderColor} ${industry.bgColor} p-6 hover:scale-105 transition-transform`}
              >
                <div className={`w-12 h-12 rounded-lg ${industry.bgColor} border ${industry.borderColor} flex items-center justify-center mb-4`}>
                  <Icon className={`w-6 h-6 ${industry.color}`} />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{industry.name}</h3>
                <ul className="space-y-2">
                  {industry.useCases.map((useCase, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                      <span className={`${industry.color} mt-1`}>•</span>
                      <span>{useCase}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

