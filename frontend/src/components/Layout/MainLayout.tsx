/**
 * Main layout component
 */

import { WorkflowCanvas } from '@/components/Canvas/WorkflowCanvas';
import { UtilitySidebar } from '@/components/Sidebar/UtilitySidebar';
import { ExecutionLogsSidebar } from '@/components/Sidebar/ExecutionLogsSidebar';
import { ChatInterface } from '@/components/Chat/ChatInterface';
import { UtilityModal } from '@/components/Sidebar/UtilityModal';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/utils/cn';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export function MainLayout() {
  const { nodePaletteOpen, chatInterfaceOpen, toggleChatInterface, toggleNodePalette } = useUIStore();

  return (
    <div className="h-full flex relative">
      {/* Sidebar Toggle Button */}
      <button
        onClick={toggleNodePalette}
        className={cn(
          'absolute left-0 top-1/2 -translate-y-1/2 z-50 bg-slate-800/90 border border-white/10 rounded-r-lg p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/90 transition-all',
          nodePaletteOpen && 'translate-x-64'
        )}
        title={nodePaletteOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        {nodePaletteOpen ? (
          <ChevronLeft className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </button>

      {/* Left Sidebar - Empty space with utility icons at bottom */}
      <div
        className={cn(
          'transition-all duration-300 ease-in-out flex flex-col border-r border-white/10 glass-strong',
          nodePaletteOpen ? 'w-64' : 'w-0 overflow-hidden'
        )}
      >
        {nodePaletteOpen && <UtilitySidebar />}
      </div>

      {/* Canvas Area */}
      <div className="flex-1 h-full relative">
        <WorkflowCanvas />
      </div>

      {/* Execution Logs Sidebar (Right) */}
      <ExecutionLogsSidebar />
      
      {/* Chat Interface (Bottom-Right Overlay) */}
      <ChatInterface 
        isOpen={chatInterfaceOpen} 
        onClose={toggleChatInterface} 
      />
      
      {/* Utility Modals (Full-page overlays) */}
      <UtilityModal />
    </div>
  );
}

