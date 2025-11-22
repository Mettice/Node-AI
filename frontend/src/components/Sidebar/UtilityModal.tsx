/**
 * Utility Modal - Full-page modal for utility panels
 */

import { X } from 'lucide-react';
import { useUIStore } from '@/store/uiStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { ModelRegistry } from './ModelRegistry';
import { RAGEvaluationPanel } from '@/components/RAGEvaluation/RAGEvaluationPanel';
import { PromptPlayground } from '@/components/PromptPlayground/PromptPlayground';
import { RAGOptimizationPanel } from '@/components/RAGOptimization/RAGOptimizationPanel';
import { Dashboard } from '@/components/Dashboard/Dashboard';
import { KnowledgeBaseManager } from '@/components/KnowledgeBase/KnowledgeBaseManager';
import { SettingsPanel } from '@/components/Settings/SettingsPanel';
import { cn } from '@/utils/cn';

const modalTitles: Record<string, string> = {
  'rag-eval': 'RAG Evaluation',
  'prompt': 'Prompt Builder',
  'models': 'Model Registry',
  'optimize': 'Auto-tune RAG',
  'knowledge-base': 'Knowledge Base Manager',
  'dashboard': 'Metrics Dashboard',
  'templates': 'Workflow Templates',
  'help': 'Help & Documentation',
  'settings': 'Settings',
};

export function UtilityModal() {
  const { activeUtility, setActiveUtility } = useUIStore();
  const { workflowId } = useWorkflowStore();

  if (!activeUtility) return null;

  const handleClose = () => {
    setActiveUtility(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleClose();
    }
  };

  const renderContent = () => {
    switch (activeUtility) {
      case 'rag-eval':
        return <RAGEvaluationPanel />;
      case 'prompt':
        return <PromptPlayground />;
      case 'models':
        return <ModelRegistry />;
      case 'optimize':
        return <RAGOptimizationPanel />;
      case 'knowledge-base':
        return <KnowledgeBaseManager />;
      case 'dashboard':
        return <Dashboard workflowId={workflowId || undefined} />;
      case 'templates':
        return (
          <div className="h-full flex items-center justify-center text-slate-400">
            <p>Templates coming soon...</p>
          </div>
        );
      case 'help':
        return (
          <div className="h-full flex items-center justify-center text-slate-400">
            <p>Help & Documentation coming soon...</p>
          </div>
        );
      case 'settings':
        return <SettingsPanel />;
      default:
        return null;
    }
  };

  return (
    <>
      {/* Backdrop - only covers canvas area, not sidebar */}
      <div
        className="fixed top-0 bottom-0 right-0 bg-black/60 backdrop-blur-sm z-40"
        style={{ left: '256px' }} // Start after sidebar (256px = w-64)
        onClick={handleClose}
        onKeyDown={handleKeyDown}
      />

      {/* Side Panel - appears next to sidebar, keeping sidebar visible */}
      <div
        className={cn(
          'fixed top-0 right-0 bottom-0 z-50 flex flex-col',
          'bg-slate-900/98 backdrop-blur-lg border-l border-white/10',
          activeUtility === 'dashboard' ? 'w-[800px]' : 'w-[600px]',
          'shadow-2xl',
          'transition-all duration-300 ease-out'
        )}
        style={{
          animation: 'slideInFromRight 0.3s ease-out',
        }}
        onKeyDown={handleKeyDown}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between flex-shrink-0">
          <h2 className="text-xl font-semibold text-white">
            {modalTitles[activeUtility] || 'Utility'}
          </h2>
          <button
            onClick={handleClose}
            className="text-slate-400 hover:text-white transition-colors p-2 hover:bg-white/5 rounded-lg"
            title="Close (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {renderContent()}
        </div>
      </div>
    </>
  );
}

