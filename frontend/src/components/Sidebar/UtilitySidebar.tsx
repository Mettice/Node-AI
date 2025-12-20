/**
 * Utility Sidebar - Enhanced vertical utility icons with Living Intelligence
 * Features: Hover expansion, amber active indicators, reorganized sections
 */

import { TestTube, Sparkles, GraduationCap, Zap, FileText, HelpCircle, Settings, BarChart3, Database, Layers, Bookmark } from 'lucide-react';
import { useUIStore } from '@/store/uiStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { cn } from '@/utils/cn';
import { useState } from 'react';

interface UtilityItem {
  id: string;
  icon: typeof TestTube;
  label: string;
  tab: 'rag-eval' | 'prompt' | 'models' | 'optimize' | 'templates' | 'help' | 'settings' | 'dashboard' | 'knowledge-base';
  requiresDeployment?: boolean;
  section: 'top' | 'middle' | 'bottom'; // Section organization
  description: string; // Brief description for tooltips
}

// Reorganized according to user specifications:
// Top: Nodes, Templates
// Middle: RAG, Prompt, Models  
// Bottom: Settings, Help
const utilities: UtilityItem[] = [
  // TOP SECTION - Core workflow building
  { id: 'templates', icon: Bookmark, label: 'Templates', tab: 'templates', section: 'top', description: 'Pre-built workflow templates' },
  
  // MIDDLE SECTION - AI/Intelligence tools
  { id: 'rag', icon: TestTube, label: 'RAG', tab: 'rag-eval', section: 'middle', description: 'RAG evaluation and testing' },
  { id: 'prompt', icon: Sparkles, label: 'Prompt', tab: 'prompt', section: 'middle', description: 'Prompt engineering tools' },
  { id: 'models', icon: GraduationCap, label: 'Models', tab: 'models', section: 'middle', description: 'Model registry and management' },
  { id: 'auto-tune', icon: Zap, label: 'Auto-tune', tab: 'optimize', section: 'middle', description: 'RAG optimization and tuning' },
  { id: 'knowledge-base', icon: Database, label: 'Knowledge Base', tab: 'knowledge-base', section: 'middle', description: 'Knowledge base management' },
  { id: 'dashboard', icon: BarChart3, label: 'Dashboard', tab: 'dashboard', requiresDeployment: true, section: 'middle', description: 'Performance metrics and analytics' },
  
  // BOTTOM SECTION - System and support
  { id: 'settings', icon: Settings, label: 'Settings', tab: 'settings', section: 'bottom', description: 'System settings and preferences' },
  { id: 'help', icon: HelpCircle, label: 'Help', tab: 'help', section: 'bottom', description: 'Help and documentation' },
];

// Group utilities by section
const utilitiesBySection = {
  top: utilities.filter(u => u.section === 'top'),
  middle: utilities.filter(u => u.section === 'middle'),
  bottom: utilities.filter(u => u.section === 'bottom'),
};

export function UtilitySidebar() {
  const { activeUtility, setActiveUtility } = useUIStore();
  const { workflowId } = useWorkflowStore();
  const [hoveredUtility, setHoveredUtility] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleUtilityClick = (utility: UtilityItem) => {
    // Allow clicking even if requiresDeployment - the modal will show a message
    if (activeUtility === utility.tab) {
      setActiveUtility(null); // Close if already open
    } else {
      setActiveUtility(utility.tab);
    }
  };

  const renderSection = (section: UtilityItem[], sectionName: string) => (
    <div key={sectionName} className="space-y-1">
      {section.map((utility) => {
        const Icon = utility.icon;
        const isActive = activeUtility === utility.tab;
        const isHovered = hoveredUtility === utility.id;
        const hasWarning = utility.requiresDeployment && !workflowId;

        return (
          <div
            key={utility.id}
            className="relative group"
            onMouseEnter={() => setHoveredUtility(utility.id)}
            onMouseLeave={() => setHoveredUtility(null)}
          >
            {/* Hover tooltip */}
            {isHovered && !isExpanded && (
              <div className="absolute left-full ml-3 px-3 py-2 bg-slate-800/95 backdrop-blur-sm border border-white/10 rounded-lg text-sm text-white whitespace-nowrap z-50 pointer-events-none">
                <div className="font-medium">{utility.label}</div>
                <div className="text-xs text-slate-400 mt-1">{utility.description}</div>
                {/* Arrow pointing to button */}
                <div className="absolute right-full top-3 -translate-y-1/2 border-4 border-transparent border-r-slate-800/95" />
              </div>
            )}

            <button
              onClick={() => handleUtilityClick(utility)}
              className={cn(
                'w-full flex items-center gap-3 py-3 px-3 rounded-lg',
                'transition-all duration-300 ease-out',
                'hover:bg-white/5 hover:scale-105',
                'focus:outline-none focus:ring-2 focus:ring-amber-500/50',
                // Active state with amber theme
                isActive && cn(
                  'bg-gradient-to-r from-amber-500/20 to-amber-600/10',
                  'border-l-4 border-amber-400',
                  'shadow-lg shadow-amber-500/20'
                ),
                hasWarning && 'opacity-60',
                // Hover expansion effect
                isHovered && 'bg-white/8'
              )}
              title={hasWarning ? 'Save and deploy a workflow to view metrics' : utility.description}
            >
              {/* Icon with enhanced styling */}
              <div className="relative flex-shrink-0">
                {/* Glow effect for active items */}
                {isActive && (
                  <div className="absolute inset-0 rounded-lg bg-amber-400/30 blur-lg scale-150" />
                )}
                <Icon
                  className={cn(
                    'w-5 h-5 relative z-10 transition-all duration-300',
                    isActive 
                      ? 'text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]'
                      : hasWarning 
                        ? 'text-slate-500' 
                        : 'text-slate-400 group-hover:text-white',
                    isHovered && !isActive && 'scale-110'
                  )}
                />
                
                {/* Active indicator dot */}
                {isActive && (
                  <div className="absolute -right-1 -top-1 w-2 h-2 bg-amber-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.8)]" />
                )}
              </div>

              {/* Label with expand/collapse animation */}
              <div className={cn(
                'flex flex-col transition-all duration-300 overflow-hidden',
                isExpanded ? 'opacity-100 max-w-none' : 'opacity-0 max-w-0 hidden sm:flex sm:opacity-100 sm:max-w-none'
              )}>
                <span className={cn(
                  'text-sm font-semibold transition-colors duration-300 text-left whitespace-nowrap',
                  isActive 
                    ? 'text-amber-300'
                    : hasWarning 
                      ? 'text-slate-500' 
                      : 'text-slate-300 group-hover:text-white'
                )}>
                  {utility.label}
                </span>
                {isExpanded && (
                  <span className="text-xs text-slate-500 text-left">
                    {utility.description}
                  </span>
                )}
              </div>

              {/* Expansion indicator */}
              {isHovered && !isExpanded && (
                <div className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="w-1 h-1 bg-white/40 rounded-full" />
                </div>
              )}
            </button>
          </div>
        );
      })}
    </div>
  );

  return (
    <div 
      className="flex flex-col h-full overflow-hidden"
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      {/* Navigation sections - organized by user spec */}
      <div className="flex-1 flex flex-col justify-end space-y-6 p-2">
        {/* Top Section - Nodes, Templates */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-slate-500 px-3 mb-2">
            {isExpanded ? 'BUILD' : ''}
          </div>
          {renderSection(utilitiesBySection.top, 'top')}
        </div>

        {/* Middle Section - RAG, Prompt, Models */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-slate-500 px-3 mb-2">
            {isExpanded ? 'AI TOOLS' : ''}
          </div>
          {renderSection(utilitiesBySection.middle, 'middle')}
        </div>

        {/* Bottom Section - Settings, Help */}
        <div className="space-y-1 border-t border-white/10 pt-4">
          <div className="text-xs font-medium text-slate-500 px-3 mb-2">
            {isExpanded ? 'SYSTEM' : ''}
          </div>
          {renderSection(utilitiesBySection.bottom, 'bottom')}
        </div>
      </div>
    </div>
  );
}

