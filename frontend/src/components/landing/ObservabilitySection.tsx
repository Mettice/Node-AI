import { BarChart3, TrendingUp, DollarSign, Activity, Eye, AlertTriangle } from 'lucide-react';

export function ObservabilitySection() {
  const features = [
    {
      icon: Eye,
      title: 'End-to-End Tracing',
      description: 'See every step of your workflow execution with detailed traces and spans.',
      color: 'text-blue-400',
    },
    {
      icon: DollarSign,
      title: 'Cost Forecasting',
      description: 'Predict and optimize your AI spending with intelligent cost forecasting.',
      color: 'text-green-400',
    },
    {
      icon: Activity,
      title: 'Real-Time Monitoring',
      description: 'Monitor workflow performance and health in real-time with live metrics.',
      color: 'text-purple-400',
    },
    {
      icon: BarChart3,
      title: 'Performance Analytics',
      description: 'Track token usage, latency, and success rates across all your workflows.',
      color: 'text-yellow-400',
    },
    {
      icon: AlertTriangle,
      title: 'Error Tracking',
      description: 'Identify and debug issues quickly with comprehensive error tracking.',
      color: 'text-red-400',
    },
    {
      icon: TrendingUp,
      title: 'Quality Metrics',
      description: 'Measure and improve workflow quality with built-in evaluation metrics.',
      color: 'text-cyan-400',
    },
  ];

  return (
    <section id="observability" className="py-24 bg-slate-950 border-t border-slate-900 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-3 py-1 mb-6">
              <Eye className="w-4 h-4 text-indigo-400" />
              <span className="text-xs font-medium text-indigo-300">Production Observability</span>
            </div>

            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              See Every Token, <br />
              <span className="text-indigo-400">Track Every Cost</span>
            </h2>

            <p className="text-lg text-slate-400 mb-8 leading-relaxed">
              Production-grade observability built in. Monitor, debug, and optimize your AI workflows with comprehensive tracing, cost forecasting, and performance analytics.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {features.map((feature, idx) => {
                const Icon = feature.icon;
                return (
                  <div key={idx} className="flex gap-3 p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                    <div className={`w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center flex-shrink-0`}>
                      <Icon className={`w-5 h-5 ${feature.color}`} />
                    </div>
                    <div>
                      <h3 className="text-white font-semibold text-sm mb-1">{feature.title}</h3>
                      <p className="text-xs text-slate-400">{feature.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 bg-indigo-500/20 blur-[100px] rounded-full"></div>
            <div className="relative bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl">
              <div className="space-y-6">
                {/* Mock Trace Visualization */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-sm font-semibold text-white">Execution Trace</h4>
                    <span className="text-xs text-green-400">Completed</span>
                  </div>
                  <div className="space-y-2">
                    {['Text Input', 'Vector Search', 'Rerank', 'Chat'].map((step, idx) => (
                      <div key={idx} className="flex items-center gap-3 p-2 bg-slate-950 rounded border border-slate-800">
                        <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                        <span className="text-xs text-slate-300 flex-1">{step}</span>
                        <span className="text-xs text-slate-500">{(idx + 1) * 120}ms</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Mock Cost Chart */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-sm font-semibold text-white">Cost Forecast</h4>
                    <span className="text-xs text-indigo-400">Next 30 days</span>
                  </div>
                  <div className="h-24 bg-slate-950 rounded border border-slate-800 flex items-end justify-around p-2">
                    {[40, 60, 45, 70, 55, 80, 65].map((height, idx) => (
                      <div
                        key={idx}
                        className="w-6 bg-indigo-500 rounded-t"
                        style={{ height: `${height}%` }}
                      ></div>
                    ))}
                  </div>
                  <div className="mt-2 flex justify-between text-xs text-slate-500">
                    <span>Est: $245</span>
                    <span>Current: $189</span>
                  </div>
                </div>

                {/* Mock Metrics */}
                <div className="grid grid-cols-3 gap-3 pt-4 border-t border-slate-800">
                  <div className="text-center">
                    <div className="text-lg font-bold text-white">99.2%</div>
                    <div className="text-xs text-slate-400">Success Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-white">1.2s</div>
                    <div className="text-xs text-slate-400">Avg Latency</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-white">$0.12</div>
                    <div className="text-xs text-slate-400">Per Execution</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

