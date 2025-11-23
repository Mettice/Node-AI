/**
 * Utility Sidebar - Vertical utility icons at bottom of left sidebar
 */

import { TestTube, Sparkles, GraduationCap, Zap, FileText, HelpCircle, Settings, BarChart3, Database } from 'lucide-react';
import { useUIStore } from '@/store/uiStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { cn } from '@/utils/cn';

interface UtilityItem {
  id: string;
  icon: typeof TestTube;
  label: string;
  tab: 'rag-eval' | 'prompt' | 'models' | 'optimize' | 'templates' | 'help' | 'settings' | 'dashboard' | 'knowledge-base';
  requiresDeployment?: boolean;
  color: string; // Active color for the icon
  hoverColor: string; // Hover color for the icon
  inactiveColor: string; // Inactive/dimmed color
  borderColor: string; // Border color when active
  bgColor: string; // Background color when active
}

const utilities: UtilityItem[] = [
  { id: 'rag', icon: TestTube, label: 'RAG', tab: 'rag-eval', color: 'text-blue-400', hoverColor: 'hover:text-blue-300', inactiveColor: 'text-blue-500/50', borderColor: 'border-blue-500', bgColor: 'bg-blue-500/20' },
  { id: 'prompt', icon: Sparkles, label: 'Prompt', tab: 'prompt', color: 'text-yellow-400', hoverColor: 'hover:text-yellow-300', inactiveColor: 'text-yellow-500/50', borderColor: 'border-yellow-500', bgColor: 'bg-yellow-500/20' },
  { id: 'models', icon: GraduationCap, label: 'Models', tab: 'models', color: 'text-purple-400', hoverColor: 'hover:text-purple-300', inactiveColor: 'text-purple-500/50', borderColor: 'border-purple-500', bgColor: 'bg-purple-500/20' },
  { id: 'auto-tune', icon: Zap, label: 'Auto-tune', tab: 'optimize', color: 'text-orange-400', hoverColor: 'hover:text-orange-300', inactiveColor: 'text-orange-500/50', borderColor: 'border-orange-500', bgColor: 'bg-orange-500/20' },
  { id: 'knowledge-base', icon: Database, label: 'Knowledge Base', tab: 'knowledge-base', color: 'text-green-400', hoverColor: 'hover:text-green-300', inactiveColor: 'text-green-500/50', borderColor: 'border-green-500', bgColor: 'bg-green-500/20' },
  { id: 'dashboard', icon: BarChart3, label: 'Dashboard', tab: 'dashboard', requiresDeployment: true, color: 'text-cyan-400', hoverColor: 'hover:text-cyan-300', inactiveColor: 'text-cyan-500/50', borderColor: 'border-cyan-500', bgColor: 'bg-cyan-500/20' },
  { id: 'templates', icon: FileText, label: 'Templates', tab: 'templates', color: 'text-pink-400', hoverColor: 'hover:text-pink-300', inactiveColor: 'text-pink-500/50', borderColor: 'border-pink-500', bgColor: 'bg-pink-500/20' },
  { id: 'help', icon: HelpCircle, label: 'Help', tab: 'help', color: 'text-indigo-400', hoverColor: 'hover:text-indigo-300', inactiveColor: 'text-indigo-500/50', borderColor: 'border-indigo-500', bgColor: 'bg-indigo-500/20' },
  { id: 'settings', icon: Settings, label: 'Settings', tab: 'settings', color: 'text-slate-400', hoverColor: 'hover:text-slate-300', inactiveColor: 'text-slate-500/50', borderColor: 'border-slate-500', bgColor: 'bg-slate-500/20' },
];

export function UtilitySidebar() {
  const { activeUtility, setActiveUtility } = useUIStore();
  const { workflowId } = useWorkflowStore();

  const handleUtilityClick = (utility: UtilityItem) => {
    // Allow clicking even if requiresDeployment - the modal will show a message
    if (activeUtility === utility.tab) {
      setActiveUtility(null); // Close if already open
    } else {
      setActiveUtility(utility.tab);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Empty space at top */}
      <div className="flex-1" />

      {/* Utility icons at bottom - compact design */}
      <div className="border-t border-white/10">
        {utilities.map((utility) => {
          const Icon = utility.icon;
          const isActive = activeUtility === utility.tab;
          const hasWarning = utility.requiresDeployment && !workflowId;

          return (
            <button
              key={utility.id}
              onClick={() => handleUtilityClick(utility)}
              className={cn(
                'w-full flex items-center gap-1 md:gap-2 py-2 px-2 md:px-3',
                'transition-all duration-200',
                'hover:bg-white/5',
                isActive && `${utility.bgColor} border-l-2 ${utility.borderColor}`,
                hasWarning && 'opacity-75'
              )}
              title={hasWarning ? 'Save and deploy a workflow to view metrics' : utility.label}
            >
              <Icon
                className={cn(
                  'w-3 md:w-4 h-3 md:h-4 flex-shrink-0 transition-colors',
                  isActive 
                    ? utility.color 
                    : hasWarning 
                      ? 'text-slate-500' 
                      : `${utility.inactiveColor} ${utility.hoverColor}`
                )}
              />
              <span
                className={cn(
                  'text-xs font-medium transition-colors hidden sm:block',
                  isActive 
                    ? utility.color.replace('-400', '-300') 
                    : hasWarning 
                      ? 'text-slate-500' 
                      : `${utility.inactiveColor} ${utility.hoverColor}`
                )}
              >
                {utility.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

