/**
 * Cost tracker component
 */

import { useExecutionStore } from '@/store/executionStore';

export function CostTracker() {
  const { cost } = useExecutionStore();

  const formatCost = (cost: number | undefined) => {
    if (cost === undefined || cost === null) return '$0.00';
    if (cost === 0) return '$0.00';
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(2)}`;
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-slate-400">Total Cost:</span>
      <span className="text-lg font-bold text-blue-400">
        {formatCost(cost)}
      </span>
    </div>
  );
}

