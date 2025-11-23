/**
 * Enhanced Cost Intelligence Panel
 * 
 * Features:
 * - Cost breakdown by category, provider, model
 * - Budget management and alerts
 * - Cost forecasting with trends
 * - ROI calculator
 * - Optimization suggestions
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { 
  analyzeExecutionCost, 
  getCostOptimizations,
  predictWorkflowCost,
  getCostForecast,
  getBudgetStatus,
  setBudget,
  calculateROI,
  type CostAnalysis,
  type OptimizationSuggestion,
  type CostPrediction,
  type CostForecast,
  type BudgetStatus,
} from '@/services/costIntelligence';
import { Spinner } from '@/components/common/Spinner';
import { 
  DollarSign, TrendingDown, Zap, CheckCircle2, 
  AlertTriangle, TrendingUp, BarChart3, Target, Calculator,
  PieChart, LineChart
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { toast } from 'react-hot-toast';

type Tab = 'overview' | 'breakdown' | 'budget' | 'forecast' | 'roi' | 'optimize';

export function CostIntelligence() {
  const { executionId, status } = useExecutionStore();
  const workflowId = useWorkflowStore((state) => state.workflowId);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [budgetAmount, setBudgetAmount] = useState<string>('');
  const [roiTimeSaved, setRoiTimeSaved] = useState<string>('');
  const [roiHourlyRate, setRoiHourlyRate] = useState<string>('');

  // Fetch cost analysis
  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['cost-analysis', executionId],
    queryFn: () => analyzeExecutionCost(executionId!),
    enabled: !!executionId && status === 'completed',
  });

  // Fetch optimizations
  const { data: optimizations, isLoading: optimizationsLoading } = useQuery({
    queryKey: ['cost-optimizations', executionId],
    queryFn: () => getCostOptimizations(executionId!),
    enabled: !!executionId && status === 'completed',
  });

  // Fetch cost prediction
  const { data: prediction, isLoading: predictionLoading } = useQuery({
    queryKey: ['cost-prediction', executionId],
    queryFn: () => predictWorkflowCost({ execution_id: executionId! }),
    enabled: !!executionId && status === 'completed',
  });

  // Fetch cost forecast
  const { data: forecast, isLoading: forecastLoading } = useQuery({
    queryKey: ['cost-forecast', workflowId],
    queryFn: () => getCostForecast(workflowId || '', 30),
    enabled: !!workflowId && status === 'completed',
  });

  // Fetch budget status
  const { data: budgetStatus, isLoading: budgetLoading, refetch: refetchBudget } = useQuery({
    queryKey: ['budget-status', workflowId],
    queryFn: () => getBudgetStatus(workflowId || ''),
    enabled: !!workflowId && status === 'completed',
    retry: false, // Don't retry if budget doesn't exist
  });

  // Calculate ROI
  const handleCalculateROI = async () => {
    if (!workflowId) return;
    
    try {
      const timeSaved = roiTimeSaved ? parseFloat(roiTimeSaved) : undefined;
      const hourlyRate = roiHourlyRate ? parseFloat(roiHourlyRate) : undefined;
      
      const roi = await calculateROI({
        workflow_id: workflowId,
        time_saved_hours: timeSaved,
        hourly_rate: hourlyRate,
      });
      
      toast.success(`ROI: ${roi.roi_percentage.toFixed(1)}%`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to calculate ROI');
    }
  };

  // Set budget
  const handleSetBudget = async () => {
    if (!workflowId || !budgetAmount) return;
    
    try {
      await setBudget({
        workflow_id: workflowId,
        monthly_budget: parseFloat(budgetAmount),
        alert_threshold: 0.8,
        enabled: true,
      });
      toast.success('Budget set successfully');
      setBudgetAmount('');
      refetchBudget();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to set budget');
    }
  };

  // Only show if execution is completed
  if (!executionId || status !== 'completed') {
    return (
      <div className="p-4 text-center text-slate-400">
        <DollarSign className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p className="text-sm">Run a workflow to see cost analysis</p>
      </div>
    );
  }

  if (analysisLoading || optimizationsLoading || predictionLoading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="p-4 text-center text-slate-400">
        <p className="text-sm">No cost data available</p>
      </div>
    );
  }

  const tabs: { id: Tab; label: string; icon: typeof DollarSign }[] = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'breakdown', label: 'Breakdown', icon: PieChart },
    { id: 'budget', label: 'Budget', icon: Target },
    { id: 'forecast', label: 'Forecast', icon: LineChart },
    { id: 'roi', label: 'ROI', icon: Calculator },
    { id: 'optimize', label: 'Optimize', icon: TrendingDown },
  ];

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/10 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'px-3 py-2 text-xs font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap',
                'hover:bg-white/5',
                activeTab === tab.id
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-slate-400 hover:text-slate-300'
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="space-y-4">
        {activeTab === 'overview' && (
          <OverviewTab analysis={analysis} prediction={prediction} budgetStatus={budgetStatus} />
        )}
        {activeTab === 'breakdown' && (
          <BreakdownTab analysis={analysis} />
        )}
        {activeTab === 'budget' && (
          <BudgetTab 
            budgetStatus={budgetStatus} 
            budgetLoading={budgetLoading}
            budgetAmount={budgetAmount}
            setBudgetAmount={setBudgetAmount}
            onSetBudget={handleSetBudget}
          />
        )}
        {activeTab === 'forecast' && (
          <ForecastTab forecast={forecast} forecastLoading={forecastLoading} />
        )}
        {activeTab === 'roi' && (
          <ROITab 
            roiTimeSaved={roiTimeSaved}
            setRoiTimeSaved={setRoiTimeSaved}
            roiHourlyRate={roiHourlyRate}
            setRoiHourlyRate={setRoiHourlyRate}
            onCalculateROI={handleCalculateROI}
          />
        )}
        {activeTab === 'optimize' && (
          <OptimizeTab 
            suggestions={analysis?.suggestions} 
            optimizations={optimizations || []} 
          />
        )}
      </div>
    </div>
  );
}

function OverviewTab({ 
  analysis, 
  prediction, 
  budgetStatus 
}: { 
  analysis: CostAnalysis; 
  prediction?: CostPrediction;
  budgetStatus?: BudgetStatus;
}) {
  return (
    <div className="space-y-4">
      {/* Total Cost */}
      <div className="glass rounded-lg p-4 border border-white/10">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400 mb-1">Total Cost</div>
            <div className="text-2xl font-bold text-green-400">
              ${(analysis?.total_cost || 0).toFixed(4)}
            </div>
          </div>
          <DollarSign className="w-8 h-8 text-green-400 opacity-50" />
        </div>
      </div>

      {/* Budget Alert */}
      {budgetStatus && budgetStatus.status !== 'ok' && (
        <div className={cn(
          'glass rounded-lg p-4 border',
          budgetStatus.status === 'exceeded' 
            ? 'border-red-500/50 bg-red-500/10' 
            : 'border-yellow-500/50 bg-yellow-500/10'
        )}>
          <div className="flex items-start gap-3">
            <AlertTriangle className={cn(
              'w-5 h-5 flex-shrink-0 mt-0.5',
              budgetStatus.status === 'exceeded' ? 'text-red-400' : 'text-yellow-400'
            )} />
            <div className="flex-1">
              <div className={cn(
                'text-sm font-semibold mb-1',
                budgetStatus.status === 'exceeded' ? 'text-red-400' : 'text-yellow-400'
              )}>
                Budget {budgetStatus.status === 'exceeded' ? 'Exceeded' : 'Warning'}
              </div>
              {budgetStatus.alerts.map((alert, idx) => (
                <div key={idx} className="text-xs text-slate-300">{alert}</div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Cost Prediction */}
      {prediction && (
        <div className="glass rounded-lg p-4 border border-white/10">
          <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Cost Prediction
          </h3>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div>
              <div className="text-slate-400 mb-1">Per run</div>
              <div className="text-white font-semibold">${(prediction?.estimated_cost_per_run || 0).toFixed(4)}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">100 runs</div>
              <div className="text-white font-semibold">${(prediction?.estimated_cost_100_runs || 0).toFixed(2)}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">1000 runs</div>
              <div className="text-white font-semibold">${(prediction?.estimated_cost_1000_runs || 0).toFixed(2)}</div>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-white/10 text-xs text-slate-500">
            Confidence: {Math.round(prediction.confidence * 100)}%
          </div>
        </div>
      )}

      {/* Top Cost Nodes */}
      {analysis?.top_cost_nodes?.length > 0 && (
        <div className="glass rounded-lg p-4 border border-white/10">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Top Cost Nodes</h3>
          <div className="space-y-2">
            {(analysis?.top_cost_nodes || []).map((node) => (
              <div
                key={node.node_id}
                className="flex items-center justify-between p-2 bg-white/5 rounded"
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-slate-300 truncate">
                    {node.node_type} ({node.node_id.slice(0, 8)}...)
                  </div>
                  {node.model && (
                    <div className="text-xs text-slate-500">{node.model}</div>
                  )}
                </div>
                <div className="text-sm font-medium text-green-400">
                  ${node.cost.toFixed(4)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function BreakdownTab({ analysis }: { analysis: CostAnalysis }) {
  return (
    <div className="space-y-4">
      {/* By Category */}
      {Object.keys(analysis?.cost_by_category || {}).length > 0 && (
        <div className="glass rounded-lg p-4 border border-white/10">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">By Category</h3>
          <div className="space-y-2">
            {Object.entries(analysis?.cost_by_category || {})
              .sort(([, a], [, b]) => b - a)
              .map(([category, cost]) => {
                const percentage = (cost / (analysis?.total_cost || 1)) * 100;
                return (
                  <div key={category}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-slate-300 capitalize">{category}</span>
                      <span className="text-sm font-medium text-green-400">
                        ${cost.toFixed(4)} ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-blue-400"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* By Provider */}
      {analysis?.cost_by_provider && Object.keys(analysis.cost_by_provider).length > 0 && (
        <div className="glass rounded-lg p-4 border border-white/10">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">By Provider</h3>
          <div className="space-y-2">
            {Object.entries(analysis?.cost_by_provider || {})
              .sort(([, a], [, b]) => b - a)
              .map(([provider, cost]) => {
                const percentage = (cost / (analysis?.total_cost || 1)) * 100;
                return (
                  <div key={provider} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300 capitalize">{provider}</span>
                    <span className="text-sm font-medium text-green-400">
                      ${cost.toFixed(4)} ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* By Model */}
      {analysis?.cost_by_model && Object.keys(analysis.cost_by_model).length > 0 && (
        <div className="glass rounded-lg p-4 border border-white/10">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">By Model</h3>
          <div className="space-y-2">
            {Object.entries(analysis?.cost_by_model || {})
              .sort(([, a], [, b]) => b - a)
              .map(([model, cost]) => {
                const percentage = (cost / (analysis?.total_cost || 1)) * 100;
                return (
                  <div key={model} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300 truncate flex-1">{model}</span>
                    <span className="text-sm font-medium text-green-400 ml-2">
                      ${cost.toFixed(4)} ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}

function BudgetTab({
  budgetStatus,
  budgetLoading,
  budgetAmount,
  setBudgetAmount,
  onSetBudget,
}: {
  budgetStatus?: BudgetStatus;
  budgetLoading: boolean;
  budgetAmount: string;
  setBudgetAmount: (value: string) => void;
  onSetBudget: () => void;
}) {
  if (budgetLoading) {
    return <Spinner size="md" />;
  }

  return (
    <div className="space-y-4">
      {budgetStatus ? (
        <>
          {/* Budget Status */}
          <div className={cn(
            'glass rounded-lg p-4 border',
            budgetStatus.status === 'exceeded' 
              ? 'border-red-500/50 bg-red-500/10' 
              : budgetStatus.status === 'warning'
              ? 'border-yellow-500/50 bg-yellow-500/10'
              : 'border-green-500/50 bg-green-500/10'
          )}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-200">Budget Status</h3>
              <div className={cn(
                'px-2 py-1 rounded text-xs font-medium',
                budgetStatus.status === 'exceeded' && 'bg-red-500/20 text-red-400',
                budgetStatus.status === 'warning' && 'bg-yellow-500/20 text-yellow-400',
                budgetStatus.status === 'ok' && 'bg-green-500/20 text-green-400',
              )}>
                {budgetStatus.status.toUpperCase()}
              </div>
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-slate-400">Monthly Budget</span>
                  <span className="text-sm font-semibold text-white">${(budgetStatus?.monthly_budget || 0).toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-slate-400">Current Spend</span>
                  <span className="text-sm font-semibold text-white">${(budgetStatus?.current_spend || 0).toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Remaining</span>
                  <span className="text-sm font-semibold text-green-400">${(budgetStatus?.remaining || 0).toFixed(2)}</span>
                </div>
              </div>
              <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className={cn(
                    'h-full transition-all',
                    budgetStatus.status === 'exceeded' && 'bg-red-500',
                    budgetStatus.status === 'warning' && 'bg-yellow-500',
                    budgetStatus.status === 'ok' && 'bg-green-500'
                  )}
                  style={{ width: `${Math.min(budgetStatus?.percentage_used || 0, 100)}%` }}
                />
              </div>
              <div className="text-xs text-slate-400">
                {(budgetStatus?.percentage_used || 0).toFixed(1)}% used • {budgetStatus?.days_remaining || 0} days remaining
              </div>
              {(budgetStatus?.projected_monthly_spend || 0) > 0 && (
                <div className="text-xs text-slate-400">
                  Projected monthly: ${(budgetStatus?.projected_monthly_spend || 0).toFixed(2)}
                </div>
              )}
            </div>
          </div>

          {/* Alerts */}
          {(budgetStatus?.alerts?.length || 0) > 0 && (
            <div className="glass rounded-lg p-4 border border-yellow-500/50 bg-yellow-500/10">
              <h3 className="text-sm font-semibold text-yellow-300 mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Alerts
              </h3>
              <div className="space-y-1">
                {(budgetStatus?.alerts || []).map((alert, idx) => (
                  <div key={idx} className="text-xs text-slate-300">{alert}</div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="glass rounded-lg p-4 border border-white/10">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Set Monthly Budget</h3>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Monthly Budget ($)</label>
              <input
                type="number"
                value={budgetAmount}
                onChange={(e) => setBudgetAmount(e.target.value)}
                placeholder="100.00"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              onClick={onSetBudget}
              disabled={!budgetAmount}
              className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Set Budget
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ForecastTab({ 
  forecast, 
  forecastLoading 
}: { 
  forecast?: CostForecast; 
  forecastLoading: boolean;
}) {
  if (forecastLoading) {
    return <Spinner size="md" />;
  }

  if (!forecast) {
    return (
      <div className="text-center py-8 text-slate-400 text-sm">
        No forecast data available. Run the workflow multiple times to see trends.
      </div>
    );
  }

  const trendIcon = forecast.weekly_trend === 'increasing' ? TrendingUp : 
                    forecast.weekly_trend === 'decreasing' ? TrendingDown : 
                    BarChart3;
  const TrendIcon = trendIcon;
  const trendColor = forecast.weekly_trend === 'increasing' ? 'text-red-400' :
                     forecast.weekly_trend === 'decreasing' ? 'text-green-400' :
                     'text-slate-400';

  return (
    <div className="space-y-4">
      {/* Trend Summary */}
      <div className="glass rounded-lg p-4 border border-white/10">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-200">Cost Trend</h3>
          <TrendIcon className={cn('w-5 h-5', trendColor)} />
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">Trend:</span>
            <span className={cn('font-semibold capitalize', trendColor)}>
              {forecast.weekly_trend}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Growth Rate:</span>
            <span className={cn('font-semibold', trendColor)}>
              {forecast.growth_rate > 0 ? '+' : ''}{forecast.growth_rate.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Monthly Estimates */}
      <div className="glass rounded-lg p-4 border border-white/10">
        <h3 className="text-sm font-semibold text-slate-200 mb-3">Monthly Estimates</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div className="text-slate-400 mb-1">Based on Average</div>
            <div className="text-lg font-bold text-white">${forecast.monthly_estimate.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-slate-400 mb-1">Projected</div>
            <div className="text-lg font-bold text-blue-400">${forecast.projected_monthly_cost.toFixed(2)}</div>
          </div>
        </div>
      </div>

      {/* Daily Costs */}
      {forecast.daily_costs.length > 0 && (
        <div className="glass rounded-lg p-4 border border-white/10">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Daily Costs</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {forecast.daily_costs.map((day, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <div>
                  <div className="text-slate-300">{new Date(day.date).toLocaleDateString()}</div>
                  <div className="text-xs text-slate-500">{day.runs} runs</div>
                </div>
                <div className="text-green-400 font-semibold">${day.cost.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ROITab({
  roiTimeSaved,
  setRoiTimeSaved,
  roiHourlyRate,
  setRoiHourlyRate,
  onCalculateROI,
}: {
  roiTimeSaved: string;
  setRoiTimeSaved: (value: string) => void;
  roiHourlyRate: string;
  setRoiHourlyRate: (value: string) => void;
  onCalculateROI: () => void;
}) {
  return (
    <div className="space-y-4">
      <div className="glass rounded-lg p-4 border border-white/10">
        <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <Calculator className="w-4 h-4" />
          ROI Calculator
        </h3>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Time Saved per Run (hours)</label>
            <input
              type="number"
              value={roiTimeSaved}
              onChange={(e) => setRoiTimeSaved(e.target.value)}
              placeholder="2.5"
              step="0.1"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Hourly Rate ($)</label>
            <input
              type="number"
              value={roiHourlyRate}
              onChange={(e) => setRoiHourlyRate(e.target.value)}
              placeholder="50"
              step="1"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            onClick={onCalculateROI}
            disabled={!roiTimeSaved || !roiHourlyRate}
            className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Calculate ROI
          </button>
        </div>
      </div>
      <div className="glass rounded-lg p-4 border border-white/10">
        <div className="text-xs text-slate-400 space-y-1">
          <p>• Enter time saved per workflow run</p>
          <p>• Enter your hourly rate</p>
          <p>• Calculate to see ROI percentage and payback period</p>
        </div>
      </div>
    </div>
  );
}

function OptimizeTab({ 
  suggestions, 
  optimizations 
}: { 
  suggestions: CostAnalysis['suggestions'];
  optimizations: OptimizationSuggestion[];
}) {
  const allSuggestions = [
    ...(suggestions || []).map(s => ({ ...s, priority: s.impact })),
    ...(optimizations || []),
  ];

  if (allSuggestions.length === 0) {
    return (
      <div className="glass rounded-lg p-4 border border-green-500/30 bg-green-500/10 text-center">
        <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-400" />
        <p className="text-sm text-slate-200">No optimization suggestions</p>
        <p className="text-xs text-slate-400 mt-1">Your workflow is already cost-optimized!</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {allSuggestions.map((suggestion, idx) => {
        const savings = 'estimated_savings' in suggestion 
          ? suggestion.estimated_savings 
          : suggestion.current_cost - suggestion.estimated_new_cost;
        const savingsPercent = 'savings_percentage' in suggestion
          ? suggestion.savings_percentage
          : (savings / suggestion.current_cost) * 100;

        return (
          <div
            key={idx}
            className="glass rounded-lg p-4 border border-yellow-500/30 bg-yellow-500/10"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1">
                <div className="text-sm text-slate-200 font-medium mb-1">
                  {'message' in suggestion ? suggestion.message : suggestion.reasoning}
                </div>
                <div className="text-xs text-slate-400 space-y-1">
                  <div>
                    Current: ${suggestion.current_cost.toFixed(4)} → 
                    {'estimated_new_cost' in suggestion && (
                      <> New: ${suggestion.estimated_new_cost.toFixed(4)}</>
                    )}
                  </div>
                  <div className="text-green-400 font-medium">
                    Save {savingsPercent.toFixed(0)}% (${savings.toFixed(4)})
                    {'quality_impact' in suggestion && (
                      <> • {suggestion.quality_impact} quality impact</>
                    )}
                  </div>
                </div>
              </div>
              <div className={cn(
                'px-2 py-1 rounded text-xs font-medium flex-shrink-0',
                suggestion.priority === 'high' && 'bg-red-500/20 text-red-400',
                suggestion.priority === 'medium' && 'bg-yellow-500/20 text-yellow-400',
                suggestion.priority === 'low' && 'bg-green-500/20 text-green-400',
                !suggestion.priority && 'bg-slate-500/20 text-slate-400',
              )}>
                {(suggestion.priority || 'medium').toUpperCase()}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
