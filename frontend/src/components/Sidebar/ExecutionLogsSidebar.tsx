/**
 * Execution logs sidebar - displays on the right when execution completes
 * Now with tabbed interface: Summary, Logs, Cost
 */

import { useState } from 'react';
import { X, BarChart3, List, DollarSign, ChevronRight, Search } from 'lucide-react';
import { useExecutionStore } from '@/store/executionStore';
import { useUIStore } from '@/store/uiStore';
import { ExecutionSummary } from '@/components/Execution/ExecutionSummary';
import { ExecutionLogs } from '@/components/Execution/ExecutionLogs';
import { CostIntelligence } from '@/components/Execution/CostIntelligence';
import { QueryTracer } from '@/components/Execution/QueryTracer';
import { cn } from '@/utils/cn';

type Tab = 'summary' | 'logs' | 'cost' | 'trace';

export function ExecutionLogsSidebar() {
  const { status, trace, cost, duration } = useExecutionStore();
  const { executionLogsOpen, setExecutionLogsOpen, chatInterfaceOpen } = useUIStore();
  const [activeTab, setActiveTab] = useState<Tab>('summary');
  const [isMinimized, setIsMinimized] = useState(false);

  // Check if there's execution data to show
  const hasExecutionData = status !== 'idle' && (trace.length > 0 || cost > 0 || duration > 0);
  
  // Show if explicitly opened OR if execution is running/completed/failed (but respect explicit close)
  const shouldShow = executionLogsOpen || (hasExecutionData && executionLogsOpen !== false);

  // If minimized, show as a small widget button
  if (isMinimized && hasExecutionData) {
    return (
      <div className="fixed right-4 top-1/2 -translate-y-1/2 z-40">
        <button
          onClick={() => setIsMinimized(false)}
          className="glass-strong rounded-lg p-3 border border-white/10 hover:bg-white/5 transition-all shadow-lg"
          title="Expand Execution Results"
        >
          <BarChart3 className="w-5 h-5 text-blue-400" />
        </button>
      </div>
    );
  }

  if (!shouldShow) {
    return null;
  }

  const tabs: { id: Tab; label: string; icon: typeof BarChart3 }[] = [
    { id: 'summary', label: 'Summary', icon: BarChart3 },
    { id: 'logs', label: 'Logs', icon: List },
    { id: 'cost', label: 'Cost', icon: DollarSign },
    { id: 'trace', label: 'Trace', icon: Search },
  ];

  return (
    <div 
      className={cn(
        'flex flex-col glass-strong border-l border-white/10 w-80 transition-all',
        chatInterfaceOpen 
          ? 'fixed right-0 top-0 bottom-[624px] z-30' // Position above chat when open
          : 'fixed right-0 top-0 bottom-0 z-30' // Full height when chat is closed
      )}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between flex-shrink-0">
        <h2 className="text-lg font-semibold text-slate-200">Execution Results</h2>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsMinimized(true)}
            className="text-slate-400 hover:text-slate-200 transition-colors p-1 hover:bg-white/5 rounded"
            title="Minimize"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
          <button
            onClick={() => {
              setExecutionLogsOpen(false);
              setIsMinimized(false);
            }}
            className="text-slate-400 hover:text-slate-200 transition-colors p-1 hover:bg-white/5 rounded"
            title="Close execution logs"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/10 flex-shrink-0 overflow-x-auto scrollbar-hide">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex-1 px-4 py-2.5 text-xs font-medium transition-colors relative flex-shrink-0',
                'hover:bg-white/5 flex items-center justify-center gap-1.5 whitespace-nowrap',
                activeTab === tab.id
                  ? 'text-blue-400'
                  : 'text-slate-400 hover:text-slate-300'
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-400" />
              )}
            </button>
          );
        })}
      </div>

      {/* Content - Scrollable */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
        <div className="p-4 space-y-4">
          {activeTab === 'summary' && <ExecutionSummary />}
          {activeTab === 'logs' && <ExecutionLogs />}
          {activeTab === 'cost' && <CostIntelligence />}
          {activeTab === 'trace' && <QueryTracer />}
        </div>
      </div>
    </div>
  );
}

