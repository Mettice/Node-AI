/**
 * Agent Room Conversion Suggestion Popup
 * Shows when a CrewAI node has 2+ agents but room is not expanded
 */

import { memo } from 'react';
import { X, Sparkles, ChevronRight } from 'lucide-react';
import { cn } from '@/utils/cn';

interface AgentRoomSuggestionProps {
  nodeId: string;
  agentCount: number;
  onConvert: () => void;
  onDismiss: () => void;
  position: { x: number; y: number };
  categoryColor: string;
}

export const AgentRoomSuggestion = memo(({
  nodeId,
  agentCount,
  onConvert,
  onDismiss,
  position,
  categoryColor,
}: AgentRoomSuggestionProps) => {
  return (
    <div
      className="fixed z-50 animate-in fade-in slide-in-from-bottom-4 duration-300"
      style={{
        left: `${position.x}px`,
        top: `${position.y - 120}px`,
      }}
    >
      <div
        className="relative w-72 bg-slate-900/95 backdrop-blur-xl border border-white/20 rounded-lg shadow-2xl p-4"
        style={{
          boxShadow: `0 0 30px ${categoryColor}30`,
        }}
      >
        {/* Close button */}
        <button
          onClick={onDismiss}
          className="absolute top-2 right-2 p-1 hover:bg-white/10 rounded transition-colors"
        >
          <X className="w-4 h-4 text-slate-400" />
        </button>

        {/* Content */}
        <div className="flex items-start gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{
              background: `${categoryColor}20`,
              boxShadow: `0 0 15px ${categoryColor}30`,
            }}
          >
            <Sparkles className="w-5 h-5" style={{ color: categoryColor }} />
          </div>
          
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-white mb-1">
              Convert to Agent Room?
            </h3>
            <p className="text-xs text-slate-400 mb-3">
              You have {agentCount} agents configured. Convert to Agent Room for better visualization and real-time collaboration tracking.
            </p>
            
            <div className="flex items-center gap-2">
              <button
                onClick={onConvert}
                className="flex-1 px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white text-xs font-medium rounded-lg transition-colors flex items-center justify-center gap-1.5"
                style={{
                  boxShadow: `0 0 15px ${categoryColor}30`,
                }}
              >
                <span>Convert Now</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={onDismiss}
                className="px-3 py-1.5 text-slate-400 hover:text-white text-xs font-medium rounded-lg hover:bg-white/10 transition-colors"
              >
                Later
              </button>
            </div>
          </div>
        </div>

        {/* Arrow pointing to node */}
        <div
          className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent"
          style={{
            borderTopColor: 'rgba(15, 23, 42, 0.95)',
          }}
        />
      </div>
    </div>
  );
});

AgentRoomSuggestion.displayName = 'AgentRoomSuggestion';

