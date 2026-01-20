import { Check, Zap, Building2, Rocket } from 'lucide-react';
import { Link } from 'react-router-dom';

export function PricingSection() {
  const plans = [
    {
      name: 'Free',
      subtitle: 'Getting started',
      price: 'Free',
      period: '',
      billing: '',
      description: 'Individual',
      icon: Zap,
      features: [
        '1 User',
        '5 Workflows',
        '2,500 executions/month',
        'All node types',
        'Community support',
        'Basic observability',
      ],
      cta: 'Start free',
      note: 'No card needed',
      popular: false,
    },
    {
      name: 'Starter',
      subtitle: 'Solo builders',
      price: '€19',
      period: '/mo',
      billing: 'billed yearly',
      description: '',
      icon: Zap,
      features: [
        '1 User',
        'Unlimited workflows',
        '2,500 executions/month',
        'Unlimited steps',
        'Cost tracking',
        'RAG evaluation (limited)',
      ],
      cta: 'Start free',
      note: 'No card needed',
      popular: false,
    },
    {
      name: 'Pro',
      subtitle: 'Most popular',
      price: '€39',
      period: '/mo',
      billing: 'billed yearly',
      description: '',
      icon: Rocket,
      features: [
        '3 Users',
        '10,000 executions/month',
        'Unlimited steps',
        'Advanced analytics',
        'Cost optimization',
        'RAG evaluation',
      ],
      cta: 'Start free',
      note: 'No card needed',
      popular: true,
    },
    {
      name: 'Business',
      subtitle: 'Teams & scale',
      price: '€499',
      period: '/mo',
      billing: 'billed yearly',
      description: '',
      icon: Building2,
      features: [
        '10 Users',
        '40,000 executions/month',
        'Unlimited steps',
        'Team collaboration',
        'RBAC',
        'Advanced analytics',
      ],
      cta: 'Start free',
      note: 'No card needed',
      popular: false,
    },
    {
      name: 'Enterprise',
      subtitle: 'Custom needs',
      price: 'Contact',
      period: '',
      billing: '',
      description: 'Custom pricing',
      icon: Building2,
      features: [
        'Unlimited users',
        'Custom limits',
        'SSO & RBAC',
        'Custom SLAs',
        '24/7 support',
        'On-premise option',
      ],
      cta: 'Contact sales',
      note: '',
      popular: false,
    },
  ];

  return (
    <section id="pricing" className="py-24 bg-slate-950 border-t border-slate-900 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-orange-500/10 border border-orange-500/20 rounded-full px-3 py-1 mb-6">
            <span className="text-xs font-medium text-orange-300">09 BUSINESS MODEL</span>
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
            Scalable SaaS Model with <span className="text-orange-400">High Gross Margins</span> and Usage-Based Revenue
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            Start free, scale as you grow. No hidden fees, no surprises.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          {plans.map((plan) => {
            const Icon = plan.icon;
            return (
              <div
                key={plan.name}
                className={`relative rounded-xl border p-6 transition-all ${
                  plan.popular
                    ? 'border-orange-500 bg-orange-500/5 scale-105 shadow-2xl shadow-orange-500/20'
                    : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-orange-500 text-white px-4 py-1 rounded-full text-xs font-semibold">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${
                    plan.popular ? 'bg-orange-500/20' : 'bg-slate-800'
                  }`}>
                    <Icon className={`w-6 h-6 ${plan.popular ? 'text-orange-400' : 'text-slate-400'}`} />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-1">{plan.name}</h3>
                  {plan.subtitle && (
                    <p className="text-slate-400 text-xs mb-2">{plan.subtitle}</p>
                  )}
                  {plan.description && (
                    <p className="text-slate-400 text-sm mb-3">{plan.description}</p>
                  )}
                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-3xl font-bold text-white">{plan.price}</span>
                    {plan.period && (
                      <span className="text-slate-400 text-sm">{plan.period}</span>
                    )}
                  </div>
                  {plan.billing && (
                    <p className="text-slate-500 text-xs mb-4">{plan.billing}</p>
                  )}
                </div>

                <ul className="space-y-2.5 mb-6">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2.5">
                      <Check className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
                        plan.popular ? 'text-orange-400' : 'text-orange-400'
                      }`} />
                      <span className="text-xs text-slate-300">{feature}</span>
                    </li>
                  ))}
                </ul>

                <div>
                  <Link
                    to={plan.name === 'Enterprise' ? '/contact' : '/register'}
                    className={`block w-full text-center py-2.5 px-4 rounded-lg font-semibold text-sm transition-all ${
                      plan.name === 'Enterprise'
                        ? 'bg-transparent text-orange-400 hover:text-orange-300 border-2 border-orange-400 hover:border-orange-300'
                        : plan.popular
                        ? 'bg-orange-500 text-white hover:bg-orange-600'
                        : 'bg-orange-500 text-white hover:bg-orange-600'
                    }`}
                  >
                    {plan.cta}
                  </Link>
                  {plan.note && (
                    <p className="text-xs text-slate-500 text-center mt-2">{plan.note}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-16 text-center">
          <p className="text-slate-400 mb-4">
            All plans include: Visual workflow builder, 30+ node types, Real-time execution, API access
          </p>
          <p className="text-sm text-slate-500">
            Need help choosing? <Link to="/contact" className="text-indigo-400 hover:text-indigo-300">Contact our team</Link>
          </p>
        </div>
      </div>
    </section>
  );
}

