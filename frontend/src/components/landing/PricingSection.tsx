import { Check, Zap, Building2, Rocket } from 'lucide-react';
import { Link } from 'react-router-dom';

export function PricingSection() {
  const plans = [
    {
      name: 'Developer',
      price: '$0',
      period: 'forever',
      description: 'Perfect for building and testing',
      icon: Zap,
      features: [
        'Unlimited workflows',
        '10,000 executions/month',
        'All node types',
        'Community support',
        'Basic observability',
        'Public API access',
      ],
      cta: 'Start Building',
      popular: false,
    },
    {
      name: 'Pro',
      price: '$99',
      period: 'per month',
      description: 'For production applications',
      icon: Rocket,
      features: [
        'Everything in Developer',
        '100,000 executions/month',
        'Advanced observability',
        'Priority support',
        'Custom integrations',
        'SLA guarantee',
        'Cost forecasting',
        'Team collaboration',
      ],
      cta: 'Start Free Trial',
      popular: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For large-scale deployments',
      icon: Building2,
      features: [
        'Everything in Pro',
        'Unlimited executions',
        'Dedicated infrastructure',
        '24/7 support',
        'Custom SLAs',
        'VPC peering',
        'SSO & RBAC',
        'Audit logs (SIEM)',
        'On-premise option',
        'Custom contracts',
      ],
      cta: 'Contact Sales',
      popular: false,
    },
  ];

  return (
    <section id="pricing" className="py-24 bg-slate-950 border-t border-slate-900 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-3 py-1 mb-6">
            <span className="text-xs font-medium text-indigo-300">Simple Pricing</span>
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
            Pricing That <span className="text-indigo-400">Scales With You</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            Start free, scale as you grow. No hidden fees, no surprises.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => {
            const Icon = plan.icon;
            return (
              <div
                key={plan.name}
                className={`relative rounded-xl border p-8 transition-all ${
                  plan.popular
                    ? 'border-indigo-500 bg-indigo-500/5 scale-105 shadow-2xl shadow-indigo-500/20'
                    : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-indigo-500 text-white px-4 py-1 rounded-full text-xs font-semibold">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${
                    plan.popular ? 'bg-indigo-500/20' : 'bg-slate-800'
                  }`}>
                    <Icon className={`w-6 h-6 ${plan.popular ? 'text-indigo-400' : 'text-slate-400'}`} />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
                  <p className="text-slate-400 text-sm mb-4">{plan.description}</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-white">{plan.price}</span>
                    {plan.period && (
                      <span className="text-slate-400 text-sm">/{plan.period}</span>
                    )}
                  </div>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <Check className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                        plan.popular ? 'text-indigo-400' : 'text-green-400'
                      }`} />
                      <span className="text-sm text-slate-300">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  to={plan.name === 'Enterprise' ? '/contact' : '/register'}
                  className={`block w-full text-center py-3 px-6 rounded-lg font-semibold transition-all ${
                    plan.popular
                      ? 'bg-indigo-500 text-white hover:bg-indigo-600'
                      : 'bg-slate-800 text-white hover:bg-slate-700 border border-slate-700'
                  }`}
                >
                  {plan.cta}
                </Link>
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

