/**
 * Agent Room Component - Visualizes multi-agent systems
 * Shows agents in a "room" with conversation flow visualization
 */

import { memo, useState, useMemo, useEffect, useRef } from 'react';
import { Handle, Position } from 'reactflow';
import { cn } from '@/utils/cn';
import { NODE_CATEGORY_COLORS } from '@/constants';
import { useExecutionStore } from '@/store/executionStore';
import { Home, ChevronDown, ChevronUp, X, MessageSquare, Target, BookOpen, Edit, Play, Pause, SkipForward, SkipBack, RotateCcw, BarChart3, Clock, DollarSign, LayoutGrid, LayoutList, Brain, Wrench, CheckCircle2, Loader2, FileText } from 'lucide-react';

const MAX_AGENTS_PER_ROOM = 4;

export interface Agent {
  role: string;
  goal?: string;
  backstory?: string;
}

interface NodeSSEEvent {
  event_type: string;
  message: string;
  timestamp: string;
  progress?: number;
  agent?: string; // Agent name/role from SSE event
  task?: string; // Task name from SSE event
  input_tokens?: number; // Input tokens used
  output_tokens?: number; // Output tokens used
  total_tokens?: number; // Total tokens used
  data?: {
    thought?: string;
    tool?: string;
    tokens_used?: {
      input_tokens?: number;
      output_tokens?: number;
      total_tokens?: number;
      input?: number;
      output?: number;
      total?: number;
    };
    [key: string]: any;
  };
}

interface AgentRoomProps {
  agents: Agent[];
  roomName?: string;
  isExpanded: boolean;
  onToggleExpand: () => void;
  status: 'idle' | 'running' | 'completed' | 'failed';
  activeAgentIndex?: number;
  progress?: number;
  cost?: number;
  categoryColor: string;
  nodeId: string;
  selected?: boolean;
  nodeEvents?: NodeSSEEvent[]; // Execution events for conversation visualization
  onEditNode?: () => void; // Callback to open node edit modal
}

// Agent role icons mapping
const getAgentIcon = (role: string, index: number): string => {
  const roleLower = role.toLowerCase();
  if (roleLower.includes('research')) return '🔍';
  if (roleLower.includes('writer') || roleLower.includes('write')) return '✍️';
  if (roleLower.includes('editor') || roleLower.includes('edit')) return '📝';
  if (roleLower.includes('analyst') || roleLower.includes('analyze')) return '📊';
  if (roleLower.includes('manager') || roleLower.includes('manage')) return '👔';
  if (roleLower.includes('developer') || roleLower.includes('code')) return '💻';
  if (roleLower.includes('designer') || roleLower.includes('design')) return '🎨';
  if (roleLower.includes('reviewer') || roleLower.includes('review')) return '👁️';
  
  // Default icons based on index
  const defaultIcons = ['🤖', '👤', '🧠', '⚡'];
  return defaultIcons[index % defaultIcons.length];
};

// Agent Details Popover Component
const AgentDetailsPopover = memo(({
  agent,
  agentIndex,
  categoryColor,
  nodeEvents = [],
  nodeId,
  onClose,
  onEditNode,
}: {
  agent: Agent;
  agentIndex: number;
  categoryColor: string;
  nodeEvents: NodeSSEEvent[];
  nodeId?: string;
  onClose: () => void;
  onEditNode?: () => void;
}) => {
  const { results } = useExecutionStore();
  
  // Get agent outputs from execution results
  const agentOutputs = useMemo(() => {
    if (!nodeId) return null;
    const result = results[nodeId];
    if (!result?.output?.agent_outputs) return null;
    
    // Find outputs for this specific agent
    const agentRole = agent.role;
    const outputs = result.output.agent_outputs[agentRole];
    
    if (Array.isArray(outputs) && outputs.length > 0) {
      return outputs;
    }
    
    // Try case-insensitive match
    const matchingKey = Object.keys(result.output.agent_outputs).find(
      key => key.toLowerCase() === agentRole.toLowerCase()
    );
    if (matchingKey) {
      return result.output.agent_outputs[matchingKey];
    }
    
    return null;
  }, [nodeId, agent.role, results]);
  
  // Filter events related to this agent
  const agentMessages = useMemo(() => {
    return nodeEvents
      .filter(event => {
        const message = event.message?.toLowerCase() || '';
        const role = agent.role.toLowerCase();
        return message.includes(role) || event.message?.includes(agent.role);
      })
      .slice(-5) // Last 5 messages
      .reverse();
  }, [nodeEvents, agent.role]);

  return (
    <div
      data-agent-popover
      className="absolute z-50 w-80 bg-slate-900/95 backdrop-blur-xl border border-white/20 rounded-lg shadow-2xl p-4"
      style={{
        boxShadow: `0 0 4px ${categoryColor}10`, // Much reduced glow
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-lg"
            style={{ backgroundColor: `${categoryColor}20` }}
          >
            {getAgentIcon(agent.role, agentIndex)}
          </div>
          <div>
            <div className="text-sm font-semibold text-white">{agent.role}</div>
            <div className="text-xs text-slate-400">Agent Details</div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {onEditNode && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEditNode();
                onClose();
              }}
              className="p-1.5 hover:bg-white/10 rounded transition-colors"
              title="Edit agent configuration"
            >
              <Edit className="w-4 h-4 text-slate-300 hover:text-white" />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded transition-colors"
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {agent.goal && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300 mb-1">
              <Target className="w-3 h-3" />
              Goal
            </div>
            <div className="text-xs text-slate-400 bg-white/5 rounded p-2">
              {agent.goal}
            </div>
          </div>
        )}

        {agent.backstory && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300 mb-1">
              <BookOpen className="w-3 h-3" />
              Backstory
            </div>
            <div className="text-xs text-slate-400 bg-white/5 rounded p-2 max-h-24 overflow-y-auto">
              {agent.backstory}
            </div>
          </div>
        )}

        {/* Agent Outputs Indicator - Link to Execution Results */}
        {agentOutputs && Array.isArray(agentOutputs) && agentOutputs.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300 mb-1">
              <FileText className="w-3 h-3" />
              Outputs Available
            </div>
            <div className="text-xs text-slate-400 bg-white/5 rounded p-2 border border-white/10">
              <div className="mb-1">
                {agentOutputs.length} task{agentOutputs.length !== 1 ? 's' : ''} completed
              </div>
              <div className="text-[10px] text-slate-500 italic">
                View full outputs in Execution Results panel
              </div>
            </div>
          </div>
        )}

        {agentMessages.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300 mb-1">
              <MessageSquare className="w-3 h-3" />
              Recent Messages ({agentMessages.length})
            </div>
            <div className="space-y-1.5 max-h-32 overflow-y-auto">
              {agentMessages.map((event, idx) => (
                <div
                  key={idx}
                  className="text-xs text-slate-400 bg-white/5 rounded p-2 border-l-2"
                  style={{ borderColor: categoryColor }}
                >
                  <div className="text-[10px] text-slate-500 mb-0.5">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </div>
                  <div className="line-clamp-2">{event.message}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

AgentDetailsPopover.displayName = 'AgentDetailsPopover';

export const AgentRoom = memo(({
  agents,
  roomName,
  isExpanded,
  onToggleExpand,
  status,
  activeAgentIndex,
  progress = 0,
  cost,
  categoryColor,
  nodeId,
  selected,
  nodeEvents = [],
  onEditNode,
}: AgentRoomProps) => {
  // Limit to max agents
  const displayAgents = agents.slice(0, MAX_AGENTS_PER_ROOM);
  const isRunning = status === 'running';
  const isCompleted = status === 'completed';
  const [selectedAgentIndex, setSelectedAgentIndex] = useState<number | null>(null);
  const [layout, setLayout] = useState<'linear' | 'circular' | 'hierarchy'>('linear');

  // Close popover when clicking outside
  const handleRoomClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    
    // Don't handle clicks on agent cards, popovers, or interactive elements
    if (
      target.closest('[data-agent-popover]') ||
      target.closest('[data-agent-card]') ||
      target.closest('button') ||
      target.closest('input') ||
      target.closest('textarea') ||
      target.closest('select')
    ) {
      e.stopPropagation(); // Prevent ReactFlow node selection
      return;
    }
    
    // Close popover if clicking outside
    if (selectedAgentIndex !== null) {
      setSelectedAgentIndex(null);
    }
    
    // Prevent ReactFlow from selecting the node when clicking on the room
    e.stopPropagation();
  };

  // Timeline replay state
  const [isReplaying, setIsReplaying] = useState(false);
  const [replayIndex, setReplayIndex] = useState<number | null>(null);
  const replayIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Extract conversation messages from events with proper agent identification
  const conversationMessages = useMemo(() => {
    if (!nodeEvents || nodeEvents.length === 0) return [];
    
    return nodeEvents
      .filter(event => event.message && event.message.trim())
      .map(event => {
        // First try to match using agent field from SSE event
        let agentIndex = -1;
        if (event.agent) {
          const agentName = event.agent.toLowerCase();
          for (let i = 0; i < agents.length; i++) {
            const role = agents[i].role.toLowerCase();
            // Match by exact role or if agent name contains role
            if (agentName === role || agentName.includes(role) || role.includes(agentName)) {
              agentIndex = i;
              break;
            }
          }
        }
        
        // Fallback: try to identify from message content
        if (agentIndex === -1) {
          const message = event.message.toLowerCase();
          for (let i = 0; i < agents.length; i++) {
            if (message.includes(agents[i].role.toLowerCase())) {
              agentIndex = i;
              break;
            }
          }
        }
        
        return {
          ...event,
          agentIndex,
        };
      })
      .slice(-10) // Last 10 messages
      .reverse();
  }, [nodeEvents, agents]);

  // Timeline messages for replay (all messages, not just last 10)
  const timelineMessages = useMemo(() => {
    if (!nodeEvents || nodeEvents.length === 0) return [];
    return nodeEvents
      .filter(event => event.message && event.message.trim())
      .map((event, idx) => {
        // First try to match using agent field from SSE event
        let agentIndex = -1;
        if (event.agent) {
          const agentName = event.agent.toLowerCase();
          for (let i = 0; i < agents.length; i++) {
            const role = agents[i].role.toLowerCase();
            // Match by exact role or if agent name contains role
            if (agentName === role || agentName.includes(role) || role.includes(agentName)) {
              agentIndex = i;
              break;
            }
          }
        }
        
        // Fallback: try to identify from message content
        if (agentIndex === -1) {
          const message = event.message.toLowerCase();
          for (let i = 0; i < agents.length; i++) {
            if (message.includes(agents[i].role.toLowerCase())) {
              agentIndex = i;
              break;
            }
          }
        }
        
        return {
          ...event,
          agentIndex,
          originalIndex: idx,
        };
      });
  }, [nodeEvents, agents]);

  // Helper function to get agent status and activity from events
  const getAgentStatus = useMemo(() => {
    return (agentIndex: number) => {
      if (!nodeEvents || nodeEvents.length === 0) {
        return { status: 'idle', task: null, tool: null, thought: null, lastEvent: null };
      }

      // Find all events for this agent
      const agentEvents = nodeEvents
        .filter(event => {
          if (event.agent) {
            const agentName = event.agent.toLowerCase();
            const role = agents[agentIndex]?.role.toLowerCase();
            return agentName === role || agentName.includes(role) || role.includes(agentName);
          }
          // Fallback to message matching
          const message = event.message?.toLowerCase() || '';
          return message.includes(agents[agentIndex]?.role.toLowerCase() || '');
        })
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

      if (agentEvents.length === 0) {
        return { status: 'idle', task: null, tool: null, thought: null, lastEvent: null };
      }

      const lastEvent = agentEvents[0];
      const eventType = lastEvent.event_type;

      // Determine status based on event type - prioritize thinking/working states
      let status: 'idle' | 'thinking' | 'working' | 'using_tool' | 'completed' = 'idle';
      
      // Check for thinking events first (most important for visibility)
      const hasThinkingEvent = agentEvents.some(e => e.event_type === 'agent_thinking');
      if (hasThinkingEvent) {
        status = 'thinking';
      } else if (eventType === 'agent_started' || eventType === 'task_started') {
        status = 'working';
      } else if (eventType === 'agent_tool_called') {
        status = 'using_tool';
      } else if (eventType === 'agent_output' || eventType === 'node_progress' || eventType === 'task_completed') {
        status = 'working';
      } else if (eventType === 'agent_completed') {
        // Mark as completed when agent_completed event is received
        status = 'completed';
      } else if (isRunning && agentIndex === activeAgentIndex) {
        status = 'working';
      } else if (isRunning && agentEvents.length > 0) {
        // If we have events and execution is running, show as working
        status = 'working';
      }
      
      // If execution is completed and agent has events, mark as completed
      if (isCompleted && agentEvents.length > 0 && status !== 'completed') {
        // Check if agent has a completed event
        const hasCompletedEvent = agentEvents.some(e => e.event_type === 'agent_completed' || e.event_type === 'task_completed');
        if (hasCompletedEvent || !isRunning) {
          status = 'completed';
        }
      }

      // Extract thought/output from various event types - prioritize actual content over task names
      let thought = null;
      let output = null;
      
      // Look for actual thoughts/outputs in events (prioritize most recent)
      for (const evt of agentEvents) {
        if (evt.data?.thought) {
          thought = evt.data.thought;
          break; // Use most recent thought
        }
        if (evt.data?.output) {
          output = evt.data.output;
          break; // Use most recent output
        }
        if (evt.data?.result) {
          output = evt.data.result;
          break; // Use most recent result
        }
        if (evt.message && evt.message.length > 20 && !evt.message.toLowerCase().includes('task:')) { 
          // Only use substantial messages that aren't just task names
          output = evt.message;
        }
      }
      
      // If no thought/output found, use the last event's message if it's substantial
      if (!thought && !output && lastEvent.message && lastEvent.message.length > 20 && 
          !lastEvent.message.toLowerCase().includes('task:')) {
        output = lastEvent.message;
      }

      return {
        status,
        task: lastEvent.task || null,
        tool: lastEvent.data?.tool || null,
        thought: thought || output || null, // Prioritize thought, then output
        lastEvent,
      };
    };
  }, [nodeEvents, agents, isRunning, activeAgentIndex]);

  // Auto-play replay when enabled
  useEffect(() => {
    if (isReplaying && timelineMessages.length > 0) {
      if (replayIndex === null) {
        setReplayIndex(0);
      } else if (replayIndex < timelineMessages.length - 1) {
        replayIntervalRef.current = setTimeout(() => {
          setReplayIndex(prev => (prev !== null ? prev + 1 : 0));
        }, 2000); // 2 seconds per message
      } else {
        setIsReplaying(false);
      }
    } else {
      if (replayIntervalRef.current) {
        clearTimeout(replayIntervalRef.current);
        replayIntervalRef.current = null;
      }
    }

    return () => {
      if (replayIntervalRef.current) {
        clearTimeout(replayIntervalRef.current);
      }
    };
  }, [isReplaying, replayIndex, timelineMessages.length]);

  // Reset replay when status changes
  useEffect(() => {
    if (status === 'running') {
      setIsReplaying(false);
      setReplayIndex(null);
    }
  }, [status]);

  const handleReplayToggle = () => {
    if (isReplaying) {
      setIsReplaying(false);
    } else {
      setReplayIndex(0);
      setIsReplaying(true);
    }
  };

  const handleReplayReset = () => {
    setIsReplaying(false);
    setReplayIndex(null);
  };

  const handleReplayStep = (direction: 'forward' | 'back') => {
    if (replayIndex === null) {
      setReplayIndex(0);
    } else {
      const newIndex = direction === 'forward' 
        ? Math.min(replayIndex + 1, timelineMessages.length - 1)
        : Math.max(replayIndex - 1, 0);
      setReplayIndex(newIndex);
    }
    setIsReplaying(false);
  };

  const handleTimelineSeek = (index: number) => {
    setReplayIndex(index);
    setIsReplaying(false);
  };

  // Compact view (collapsed)
  if (!isExpanded) {
    return (
      <div
        className={cn(
          'relative rounded-lg border-2 transition-all duration-300',
          isRunning && 'border-transparent',
          isCompleted && 'border-green-500/50',
          !isRunning && !isCompleted && 'border-white/10',
          selected && 'ring-2 ring-blue-500 ring-offset-2 shadow-lg shadow-blue-500/50'
        )}
        style={{
          width: '190px',
          background: isRunning
            ? 'linear-gradient(135deg, rgba(13, 17, 23, 0.95) 0%, rgba(13, 17, 23, 0.9) 100%)'
            : 'rgba(13, 17, 23, 0.85)',
          backdropFilter: 'blur(20px)',
        }}
      >
        {/* Animated gradient border for running state */}
        {isRunning && (
          <div
            className="absolute inset-0 rounded-lg opacity-75"
            style={{
              background: `linear-gradient(135deg, ${categoryColor}, #f0b429, #22d3ee, ${categoryColor})`,
              backgroundSize: '300% 300%',
              animation: 'gradientShift 4s ease infinite',
              padding: '2px',
              WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
              WebkitMaskComposite: 'xor',
              maskComposite: 'exclude',
            }}
          />
        )}

        <div className="relative p-3">
          <div className="flex items-center gap-2 mb-2">
            <Home className="w-4 h-4" style={{ color: categoryColor }} />
            <span className="text-xs font-semibold text-slate-100 truncate flex-1">
              {roomName || 'Agent Room'}
            </span>
            {onEditNode && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEditNode();
                }}
                className="p-1 hover:bg-white/10 rounded transition-colors"
                title="Edit agents"
              >
                <Edit className="w-3 h-3 text-slate-300" />
              </button>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleExpand();
              }}
              className="p-0.5 hover:bg-white/10 rounded transition-colors"
              title="Expand room"
            >
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>
          </div>
          
          <div className="flex items-center gap-1.5 mb-2">
            {displayAgents.map((agent, index) => (
              <div
                key={index}
                className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center text-xs transition-all',
                  index === activeAgentIndex && isRunning
                    ? 'bg-blue-500/30 border-2 border-blue-500 scale-110'
                    : 'bg-white/5 border border-white/10'
                )}
                style={{
                  boxShadow:
                    index === activeAgentIndex && isRunning
                      ? '0 0 12px rgba(59, 130, 246, 0.5)'
                      : 'none',
                }}
                title={agent.role}
              >
                {getAgentIcon(agent.role, index)}
              </div>
            ))}
            {agents.length > MAX_AGENTS_PER_ROOM && (
              <span className="text-xs text-slate-500">+{agents.length - MAX_AGENTS_PER_ROOM}</span>
            )}
          </div>

          {isRunning && (
            <div className="h-1 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full transition-all duration-300 rounded-full"
                style={{
                  width: `${progress}%`,
                  background: `linear-gradient(90deg, ${categoryColor}, #f0b429)`,
                }}
              />
            </div>
          )}

          {isCompleted && (
            <div className="text-xs text-green-400 flex items-center gap-1.5 px-2 py-1 bg-green-500/10 rounded border border-green-500/20">
              <CheckCircle2 className="w-3 h-3" />
              <span>Completed</span>
            </div>
          )}
          {status === 'failed' && (
            <div className="text-xs text-red-400 flex items-center gap-1.5 px-2 py-1 bg-red-500/10 rounded border border-red-500/20">
              <span>✗</span>
              <span>Execution Failed</span>
            </div>
          )}
          {!isRunning && !isCompleted && status !== 'failed' && (
            <div className="text-xs text-slate-400 flex items-center gap-1.5 px-2 py-1 bg-slate-500/10 rounded border border-slate-500/20">
              <span>○</span>
              <span>Idle</span>
            </div>
          )}
        </div>

        {/* Handles */}
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3"
          style={{
            backgroundColor: categoryColor,
            border: '2px solid rgba(255, 255, 255, 0.8)',
            boxShadow: `0 0 3px ${categoryColor}15`, // Much reduced glow
          }}
        />
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3"
          style={{
            backgroundColor: categoryColor,
            border: '2px solid rgba(255, 255, 255, 0.8)',
            boxShadow: `0 0 3px ${categoryColor}15`, // Much reduced glow
          }}
        />
      </div>
    );
  }

  // Expanded view (room)
  return (
    <div
      className={cn(
        'relative rounded-xl border-2 transition-all duration-300 overflow-visible',
        isRunning && 'border-transparent',
        isCompleted && 'border-green-500/50',
        !isRunning && !isCompleted && 'border-white/10',
        selected && 'ring-2 ring-blue-500 ring-offset-2 shadow-lg shadow-blue-500/50'
      )}
      style={{
        width: '480px',
        minHeight: layout === 'circular' ? '350px' : layout === 'hierarchy' ? '400px' : '200px',
        background: isRunning
          ? 'linear-gradient(135deg, rgba(13, 17, 23, 0.95) 0%, rgba(13, 17, 23, 0.9) 100%)'
          : 'rgba(13, 17, 23, 0.95)',
        backdropFilter: 'blur(20px)',
      }}
      onClick={handleRoomClick}
    >
      {/* Animated gradient border for running state */}
      {isRunning && (
        <div
          className="absolute inset-0 rounded-xl opacity-75 -z-10"
          style={{
            background: `linear-gradient(135deg, ${categoryColor}, #f0b429, #22d3ee, ${categoryColor})`,
            backgroundSize: '300% 300%',
            animation: 'gradientShift 4s ease infinite',
            padding: '3px',
          }}
        />
      )}

      {/* Room Header */}
      <div
        className="px-4 py-3 flex items-center justify-between border-b border-white/8"
        style={{
          background: `linear-gradient(135deg, ${categoryColor}20 0%, ${categoryColor}08 100%)`,
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
            style={{
              background: `${categoryColor}20`,
              boxShadow: `0 0 4px ${categoryColor}10`, // Much reduced glow
            }}
          >
            <Home />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-100">
              {roomName || 'Agent Room'}
            </div>
            <div className="text-xs text-slate-400">
              {agents.length} Agent{agents.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Layout Toggle */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setLayout(prev => {
                if (prev === 'linear') return 'circular';
                if (prev === 'circular') return 'hierarchy';
                return 'linear';
              });
            }}
            className="p-1.5 hover:bg-white/10 rounded transition-colors"
            title={`Switch layout: ${layout === 'linear' ? 'circular' : layout === 'circular' ? 'hierarchy' : 'linear'}`}
          >
            {layout === 'linear' ? (
              <LayoutGrid className="w-4 h-4 text-slate-400" />
            ) : layout === 'circular' ? (
              <LayoutList className="w-4 h-4 text-slate-400" />
            ) : (
              <Home className="w-4 h-4 text-slate-400" />
            )}
          </button>
          {onEditNode && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEditNode();
              }}
              className="px-2.5 py-1.5 flex items-center gap-1.5 hover:bg-white/10 rounded-lg transition-colors text-xs font-medium text-slate-300 hover:text-white"
              title="Edit agents and configuration"
            >
              <Edit className="w-3.5 h-3.5" />
              <span>Edit</span>
            </button>
          )}
          {isRunning && (
            <div className="px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 text-xs font-medium">
              Running
            </div>
          )}
          {isCompleted && (
            <div className="px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-medium flex items-center gap-1.5">
              <CheckCircle2 className="w-3 h-3" />
              <span>Ran Successfully</span>
            </div>
          )}
          {status === 'failed' && (
            <div className="px-2 py-1 rounded-full bg-red-500/20 text-red-400 text-xs font-medium flex items-center gap-1.5">
              <span>✗</span>
              <span>Execution Failed</span>
            </div>
          )}
          {!isRunning && !isCompleted && status !== 'failed' && (
            <div className="px-2 py-1 rounded-full bg-slate-500/20 text-slate-400 text-xs font-medium flex items-center gap-1.5">
              <span>○</span>
              <span>Idle</span>
            </div>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand();
            }}
            className="p-1 hover:bg-white/10 rounded transition-colors"
            title="Collapse room"
          >
            <ChevronUp className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Agent Container - Linear or Circular Layout */}
      <div className="px-6 py-5 relative" style={{ minHeight: layout === 'circular' ? '300px' : 'auto' }}>
        {layout === 'linear' ? (
          <>
            {/* Connection line for linear layout */}
            <div
              className="absolute top-1/2 left-20 right-20 h-0.5 -translate-y-1/2 z-0"
              style={{
                background: `linear-gradient(90deg, transparent 0%, ${categoryColor}40 20%, ${categoryColor}40 80%, transparent 100%)`,
              }}
            />
            {/* Mini Agents - Linear Layout */}
            <div className="flex items-center justify-center gap-4 relative z-10">
          {displayAgents.map((agent, index) => {
            const isActive = index === activeAgentIndex && isRunning;
            const isNext = index === (activeAgentIndex ?? -1) + 1 && isRunning;
            const isSelected = selectedAgentIndex === index;
            
            // Get agent status and activity
            const agentStatus = getAgentStatus(index);
            const isActuallyActive = agentStatus.status !== 'idle' && agentStatus.status !== 'completed';
            
            // Get latest message from this agent (or current replay message)
            const currentMessage = replayIndex !== null && timelineMessages[replayIndex]?.agentIndex === index
              ? timelineMessages[replayIndex]
              : conversationMessages.find(msg => msg.agentIndex === index);
            
            const latestMessage = isReplaying || replayIndex !== null ? currentMessage : conversationMessages.find(
              msg => msg.agentIndex === index
            );
            
            // Determine if agent should be highlighted based on replay or actual status
            const isActiveInReplay = replayIndex !== null && timelineMessages[replayIndex]?.agentIndex === index;
            const shouldHighlight = isActive || isActuallyActive || (isReplaying && isActiveInReplay) || (replayIndex !== null && isActiveInReplay);

            return (
              <div key={index} className="flex items-center gap-4 relative">
                {/* Enhanced Speech bubble with status and activity */}
                {(latestMessage || agentStatus.status !== 'idle') && (isRunning || isReplaying || replayIndex !== null) && (
                  <div
                    className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 bg-slate-800/95 backdrop-blur-sm border border-white/20 rounded-lg p-2.5 shadow-lg z-20 animate-in fade-in slide-in-from-bottom-2 duration-300"
                    style={{
                      boxShadow: `0 0 4px ${categoryColor}10`, // Much reduced glow
                    }}
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className="text-[10px] font-semibold text-slate-300 truncate flex-1">
                        {agent.role}
                      </div>
                      {/* Status badge */}
                      {agentStatus.status !== 'idle' && (
                        <div className={cn(
                          "px-1.5 py-0.5 rounded text-[9px] font-medium flex items-center gap-1",
                          agentStatus.status === 'thinking' && "bg-purple-500/20 text-purple-300",
                          agentStatus.status === 'working' && "bg-blue-500/20 text-blue-300",
                          agentStatus.status === 'using_tool' && "bg-amber-500/20 text-amber-300",
                          agentStatus.status === 'completed' && "bg-green-500/20 text-green-300",
                        )}>
                          {agentStatus.status === 'thinking' && <Brain className="w-2.5 h-2.5" />}
                          {agentStatus.status === 'working' && <Loader2 className="w-2.5 h-2.5 animate-spin" />}
                          {agentStatus.status === 'using_tool' && <Wrench className="w-2.5 h-2.5" />}
                          {agentStatus.status === 'completed' && <CheckCircle2 className="w-2.5 h-2.5" />}
                          <span className="capitalize">{agentStatus.status.replace('_', ' ')}</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Task or tool info */}
                    {(agentStatus.task || agentStatus.tool) && (
                      <div className="text-[10px] text-slate-400 mb-1.5">
                        {agentStatus.task && <span>Task: {agentStatus.task}</span>}
                        {agentStatus.tool && <span className="ml-2">🔧 {agentStatus.tool}</span>}
                      </div>
                    )}
                    
                    {/* Message or thought - show more detail during execution */}
                    {(latestMessage?.message || agentStatus.thought) && (
                      <div className="text-xs text-slate-200 line-clamp-3">
                        {agentStatus.thought || latestMessage?.message}
                      </div>
                    )}
                    {/* Show task description if available and no thought/message */}
                    {!agentStatus.thought && !latestMessage?.message && agentStatus.task && (
                      <div className="text-xs text-slate-300 line-clamp-2 italic">
                        {agentStatus.task}
                      </div>
                    )}
                    
                    {/* Speech bubble tail */}
                    <div
                      className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent"
                      style={{
                        borderTopColor: 'rgba(30, 41, 59, 0.95)',
                      }}
                    />
                  </div>
                )}

                <div
                  className={cn(
                    'relative w-24 p-3 rounded-lg text-center transition-all duration-300 cursor-pointer',
                    isActive
                      ? 'bg-blue-500/20 border-2 border-blue-500 scale-105'
                      : 'bg-white/5 border border-white/10',
                    isNext && 'bg-blue-500/10 border-blue-500/50',
                    isSelected && 'ring-2 ring-offset-2',
                    'hover:bg-white/10'
                  )}
                  style={{
                      boxShadow: isActive
                        ? '0 0 4px rgba(59, 130, 246, 0.1)' // Much reduced glow
                        : isSelected
                        ? `0 0 0 2px ${categoryColor}`
                        : 'none',
                    borderColor: isSelected ? categoryColor : undefined,
                  }}
                  title={`Click to view ${agent.role} details`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedAgentIndex(isSelected ? null : index);
                  }}
                >
                  {/* Pulse animation for active agent */}
                  {isActive && (
                    <div
                      className="absolute inset-0 rounded-lg animate-pulse"
                      style={{
                        background: 'radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 70%)',
                      }}
                    />
                  )}
                  
                  {/* Particle effects for thinking agent */}
                  {shouldHighlight && isRunning && (
                    <div 
                      className="agent-thinking-particles"
                      style={{ color: categoryColor }}
                    />
                  )}

                  <div
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center text-xl mx-auto mb-2 transition-all',
                      shouldHighlight && 'scale-110'
                    )}
                    style={{
                      background: shouldHighlight ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                      border: `2px solid ${shouldHighlight ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)'}`,
                    }}
                  >
                    {getAgentIcon(agent.role, index)}
                  </div>
                  <div className="text-xs font-semibold text-slate-100 truncate">
                    {agent.role}
                  </div>
                  {shouldHighlight && isRunning && (
                    <div className="text-[10px] text-blue-400 mt-1">
                      {isReplaying || replayIndex !== null ? 'Replaying' : 'Active'}
                    </div>
                  )}
                  {isCompleted && agentStatus.status === 'completed' && (
                    <div className="text-[10px] text-green-400 mt-1 flex items-center justify-center gap-1">
                      <CheckCircle2 className="w-2.5 h-2.5" />
                      <span>Completed</span>
                    </div>
                  )}
                  {!isRunning && !isCompleted && agentStatus.status === 'idle' && (
                    <div className="text-[10px] text-slate-400 mt-1">
                      Idle
                    </div>
                  )}
                </div>

                {/* Agent Details Popover */}
                {isSelected && (
                  <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-30">
                    <AgentDetailsPopover
                      agent={agent}
                      agentIndex={index}
                      categoryColor={categoryColor}
                      nodeEvents={nodeEvents}
                      nodeId={nodeId}
                      onClose={() => setSelectedAgentIndex(null)}
                      onEditNode={onEditNode}
                    />
                  </div>
                )}

                {/* Animated arrow between agents */}
                {index < displayAgents.length - 1 && (
                  <div
                    className="relative text-slate-400 text-lg transition-all duration-300"
                    style={{
                      color: isActive ? categoryColor : 'rgba(255, 255, 255, 0.3)',
                    }}
                  >
                    <div
                      className={cn(
                        'absolute inset-0 transition-all duration-500',
                        isActive && 'animate-pulse'
                      )}
                      style={{
                        textShadow: isActive ? `0 0 4px ${categoryColor}40` : 'none', // Reduced text shadow
                      }}
                    >
                      →
                    </div>
                    {/* Animated flow indicator */}
                    {isActive && isRunning && (
                      <div
                        className="absolute inset-0 animate-ping"
                        style={{
                          color: categoryColor,
                          animation: 'ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite',
                        }}
                      >
                        →
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
            </div>
          </>
        ) : layout === 'circular' ? (
          <>
            {/* Circular Layout */}
            <div className="relative w-full h-[280px] flex items-center justify-center">
              {/* Circular connection paths */}
              <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 0 }}>
                {displayAgents.map((_, index) => {
                  if (index === displayAgents.length - 1) return null;
                  const nextIndex = (index + 1) % displayAgents.length;
                  const radius = 100;
                  const centerX = 240; // Half of container width (480px / 2)
                  const centerY = 140; // Half of container height (280px / 2)
                  const angle1 = (index * 2 * Math.PI) / displayAgents.length - Math.PI / 2;
                  const angle2 = (nextIndex * 2 * Math.PI) / displayAgents.length - Math.PI / 2;
                  const x1 = centerX + radius * Math.cos(angle1);
                  const y1 = centerY + radius * Math.sin(angle1);
                  const x2 = centerX + radius * Math.cos(angle2);
                  const y2 = centerY + radius * Math.sin(angle2);
                  
                  const isActive = index === activeAgentIndex && isRunning;
                  
                  return (
                    <path
                      key={`path-${index}`}
                      d={`M ${x1} ${y1} A ${radius} ${radius} 0 0 1 ${x2} ${y2}`}
                      fill="none"
                      stroke={isActive ? categoryColor : 'rgba(255, 255, 255, 0.2)'}
                      strokeWidth="2"
                      strokeDasharray={isActive ? "5,5" : "none"}
                      className={cn(
                        "transition-all duration-300",
                        isActive && "animate-pulse"
                      )}
                    />
                  );
                })}
              </svg>

              {/* Mini Agents in Circle */}
              <div className="relative z-10">
                {displayAgents.map((agent, index) => {
                  const isActive = index === activeAgentIndex && isRunning;
                  const isNext = index === (activeAgentIndex ?? -1) + 1 && isRunning;
                  const isSelected = selectedAgentIndex === index;
                  
                  const radius = 100;
                  const centerX = 0;
                  const centerY = 0;
                  const angle = (index * 2 * Math.PI) / displayAgents.length - Math.PI / 2;
                  const x = centerX + radius * Math.cos(angle);
                  const y = centerY + radius * Math.sin(angle);
                  
                  // Get latest message from this agent
                  const currentMessage = replayIndex !== null && timelineMessages[replayIndex]?.agentIndex === index
                    ? timelineMessages[replayIndex]
                    : conversationMessages.find(msg => msg.agentIndex === index);
                  
                  const latestMessage = isReplaying || replayIndex !== null ? currentMessage : conversationMessages.find(
                    msg => msg.agentIndex === index
                  );
                  
                  const isActiveInReplay = replayIndex !== null && timelineMessages[replayIndex]?.agentIndex === index;
                  const shouldHighlight = isActive || (isReplaying && isActiveInReplay) || (replayIndex !== null && isActiveInReplay);

                  return (
                    <div
                      key={index}
                      className="absolute"
                      style={{
                        left: `calc(50% + ${x}px)`,
                        top: `calc(50% + ${y}px)`,
                        transform: 'translate(-50%, -50%)',
                      }}
                    >
                      {/* Speech bubble for latest message */}
                      {latestMessage && (isRunning || isReplaying || replayIndex !== null) && (
                        <div
                          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-slate-800/95 backdrop-blur-sm border border-white/20 rounded-lg p-2 shadow-lg z-20 animate-in fade-in slide-in-from-bottom-2 duration-300"
                          style={{
                            boxShadow: `0 0 4px ${categoryColor}10`, // Much reduced glow
                          }}
                        >
                          <div className="text-[10px] text-slate-400 mb-1 truncate">
                            {agent.role}
                          </div>
                          <div className="text-xs text-slate-200 line-clamp-2">
                            {latestMessage.message}
                          </div>
                          <div
                            className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent"
                            style={{
                              borderTopColor: 'rgba(30, 41, 59, 0.95)',
                            }}
                          />
                        </div>
                      )}

                      <div
                        className={cn(
                          'relative w-24 p-3 rounded-lg text-center transition-all duration-300 cursor-pointer',
                          isActive
                            ? 'bg-blue-500/20 border-2 border-blue-500 scale-105'
                            : 'bg-white/5 border border-white/10',
                          isNext && 'bg-blue-500/10 border-blue-500/50',
                          isSelected && 'ring-2 ring-offset-2',
                          'hover:bg-white/10'
                        )}
                        style={{
                      boxShadow: isActive
                        ? '0 0 4px rgba(59, 130, 246, 0.1)' // Much reduced glow
                        : isSelected
                        ? `0 0 0 2px ${categoryColor}`
                        : 'none',
                          borderColor: isSelected ? categoryColor : undefined,
                        }}
                        title={`Click to view ${agent.role} details`}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedAgentIndex(isSelected ? null : index);
                        }}
                      >
                        {/* Pulse animation for active agent */}
                        {isActive && (
                          <div
                            className="absolute inset-0 rounded-lg"
                            style={{
                              background: 'radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%)', // Reduced opacity, removed pulse
                            }}
                          />
                        )}
                        
                        {/* Particle effects for thinking agent */}
                        {shouldHighlight && isRunning && (
                          <div 
                            className="agent-thinking-particles"
                            style={{ color: categoryColor }}
                          />
                        )}

                        <div
                          className={cn(
                            'w-10 h-10 rounded-full flex items-center justify-center text-xl mx-auto mb-2 transition-all',
                            shouldHighlight && 'scale-110'
                          )}
                          style={{
                            background: shouldHighlight ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                            border: `2px solid ${shouldHighlight ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)'}`,
                          }}
                        >
                          {getAgentIcon(agent.role, index)}
                        </div>
                        <div className="text-xs font-semibold text-slate-100 truncate">
                          {agent.role}
                        </div>
                        {shouldHighlight && (
                          <div className="text-[10px] text-blue-400 mt-1">
                            {isReplaying || replayIndex !== null ? 'Replaying' : isCompleted ? 'Completed' : 'Active'}
                          </div>
                        )}
                      </div>

                      {/* Agent Details Popover */}
                      {isSelected && (
                        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-30">
                          <AgentDetailsPopover
                            agent={agent}
                            agentIndex={index}
                            categoryColor={categoryColor}
                            nodeEvents={nodeEvents}
                            onClose={() => setSelectedAgentIndex(null)}
                            onEditNode={onEditNode}
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        ) : layout === 'hierarchy' ? (
          <>
            {/* Hierarchy Layout - Tree Structure */}
            <div className="relative w-full h-[320px] flex items-center justify-center">
              {/* Hierarchy tree structure */}
              <div className="relative w-full h-full flex flex-col items-center justify-center">
                {/* Root agent (first agent) at top */}
                {displayAgents.length > 0 && (() => {
                  const rootAgent = displayAgents[0];
                  const rootIndex = 0;
                  const isActive = rootIndex === activeAgentIndex && isRunning;
                  const isSelected = selectedAgentIndex === rootIndex;
                  const rootMessage = replayIndex !== null && timelineMessages[replayIndex]?.agentIndex === rootIndex
                    ? timelineMessages[replayIndex]
                    : conversationMessages.find(msg => msg.agentIndex === rootIndex);
                  const isActiveInReplay = replayIndex !== null && timelineMessages[replayIndex]?.agentIndex === rootIndex;
                  const shouldHighlight = isActive || (isReplaying && isActiveInReplay) || (replayIndex !== null && isActiveInReplay);

                  return (
                    <div className="relative mb-8">
                      {/* Speech bubble */}
                      {rootMessage && (isRunning || isReplaying || replayIndex !== null) && (
                        <div
                          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-slate-800/95 backdrop-blur-sm border border-white/20 rounded-lg p-2 shadow-lg z-20 animate-in fade-in slide-in-from-bottom-2 duration-300"
                          style={{
                            boxShadow: `0 0 4px ${categoryColor}10`, // Much reduced glow
                          }}
                        >
                          <div className="text-[10px] text-slate-400 mb-1 truncate">
                            {rootAgent.role}
                          </div>
                          <div className="text-xs text-slate-200 line-clamp-2">
                            {rootMessage.message}
                          </div>
                          <div
                            className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent"
                            style={{
                              borderTopColor: 'rgba(30, 41, 59, 0.95)',
                            }}
                          />
                        </div>
                      )}

                      {/* Root agent card */}
                      <div
                        data-agent-card
                        className={cn(
                          'relative w-24 p-3 rounded-lg text-center transition-all duration-300 cursor-pointer',
                          isActive
                            ? 'bg-blue-500/20 border-2 border-blue-500 scale-105'
                            : 'bg-white/5 border border-white/10',
                          isSelected && 'ring-2 ring-offset-2',
                          'hover:bg-white/10'
                        )}
                        style={{
                      boxShadow: isActive
                        ? '0 0 4px rgba(59, 130, 246, 0.1)' // Much reduced glow
                        : isSelected
                        ? `0 0 0 2px ${categoryColor}`
                        : 'none',
                          borderColor: isSelected ? categoryColor : undefined,
                        }}
                        title={`Click to view ${rootAgent.role} details`}
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          setSelectedAgentIndex(isSelected ? null : rootIndex);
                        }}
                        onMouseDown={(e) => {
                          e.stopPropagation();
                        }}
                      >
                        {isActive && (
                          <div
                            className="absolute inset-0 rounded-lg"
                            style={{
                              background: 'radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%)', // Reduced opacity, removed pulse
                            }}
                          />
                        )}
                        {shouldHighlight && isRunning && (
                          <div 
                            className="agent-thinking-particles"
                            style={{ color: categoryColor }}
                          />
                        )}
                        <div
                          className={cn(
                            'w-10 h-10 rounded-full flex items-center justify-center text-xl mx-auto mb-2 transition-all',
                            shouldHighlight && 'scale-110'
                          )}
                          style={{
                            background: shouldHighlight ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                            border: `2px solid ${shouldHighlight ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)'}`,
                          }}
                        >
                          {getAgentIcon(rootAgent.role, rootIndex)}
                        </div>
                        <div className="text-xs font-semibold text-slate-100 truncate">
                          {rootAgent.role}
                        </div>
                        {shouldHighlight && (
                          <div className="text-[10px] text-blue-400 mt-1">
                            {isReplaying || replayIndex !== null ? 'Replaying' : isCompleted ? 'Completed' : 'Active'}
                          </div>
                        )}
                      </div>

                      {/* Connection lines to children */}
                      {displayAgents.length > 1 && (
                        <svg className="absolute top-full left-1/2 -translate-x-1/2 w-full h-32" style={{ zIndex: 0 }}>
                          {displayAgents.slice(1).map((_, childIndex) => {
                            const actualIndex = childIndex + 1;
                            const totalChildren = displayAgents.length - 1;
                            const spacing = totalChildren > 1 ? 200 / (totalChildren - 1) : 0;
                            const childX = (childIndex * spacing) - (totalChildren > 1 ? 100 : 0);
                            const isActive = actualIndex === activeAgentIndex && isRunning;
                            
                            return (
                              <line
                                key={childIndex}
                                x1="0"
                                y1="0"
                                x2={childX}
                                y2="120"
                                stroke={isActive ? categoryColor : 'rgba(255, 255, 255, 0.2)'}
                                strokeWidth="2"
                                strokeDasharray={isActive ? 'none' : '5,5'}
                                className={cn(
                                  "transition-all duration-300",
                                  isActive && "animate-pulse"
                                )}
                              />
                            );
                          })}
                        </svg>
                      )}

                      {isSelected && (
                        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-30">
                          <AgentDetailsPopover
                            agent={rootAgent}
                            agentIndex={rootIndex}
                            categoryColor={categoryColor}
                            nodeEvents={nodeEvents}
                            onClose={() => setSelectedAgentIndex(null)}
                            onEditNode={onEditNode}
                          />
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* Child agents in a row below */}
                {displayAgents.length > 1 && (
                  <div className="relative flex items-center justify-center gap-4 mt-32">
                    {displayAgents.slice(1).map((agent, childIndex) => {
                      const actualIndex = childIndex + 1;
                      const isActive = actualIndex === activeAgentIndex && isRunning;
                      const isSelected = selectedAgentIndex === actualIndex;
                      const childMessage = replayIndex !== null && timelineMessages[replayIndex]?.agentIndex === actualIndex
                        ? timelineMessages[replayIndex]
                        : conversationMessages.find(msg => msg.agentIndex === actualIndex);
                      const isActiveInReplay = replayIndex !== null && timelineMessages[replayIndex]?.agentIndex === actualIndex;
                      const shouldHighlight = isActive || (isReplaying && isActiveInReplay) || (replayIndex !== null && isActiveInReplay);

                      return (
                        <div key={actualIndex} className="relative">
                          {/* Speech bubble */}
                          {childMessage && (isRunning || isReplaying || replayIndex !== null) && (
                            <div
                              className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-slate-800/95 backdrop-blur-sm border border-white/20 rounded-lg p-2 shadow-lg z-20 animate-in fade-in slide-in-from-bottom-2 duration-300"
                              style={{
                                boxShadow: `0 0 4px ${categoryColor}10`, // Much reduced glow
                              }}
                            >
                              <div className="text-[10px] text-slate-400 mb-1 truncate">
                                {agent.role}
                              </div>
                              <div className="text-xs text-slate-200 line-clamp-2">
                                {childMessage.message}
                              </div>
                              <div
                                className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent"
                                style={{
                                  borderTopColor: 'rgba(30, 41, 59, 0.95)',
                                }}
                              />
                            </div>
                          )}

                          {/* Child agent card */}
                          <div
                            data-agent-card
                            className={cn(
                              'relative w-24 p-3 rounded-lg text-center transition-all duration-300 cursor-pointer',
                              isActive
                                ? 'bg-blue-500/20 border-2 border-blue-500 scale-105'
                                : 'bg-white/5 border border-white/10',
                              isSelected && 'ring-2 ring-offset-2',
                              'hover:bg-white/10'
                            )}
                            style={{
                      boxShadow: isActive
                        ? '0 0 4px rgba(59, 130, 246, 0.1)' // Much reduced glow
                        : isSelected
                        ? `0 0 0 2px ${categoryColor}`
                        : 'none',
                              borderColor: isSelected ? categoryColor : undefined,
                            }}
                            title={`Click to view ${agent.role} details`}
                            onClick={(e) => {
                              e.stopPropagation();
                              e.preventDefault();
                              setSelectedAgentIndex(isSelected ? null : actualIndex);
                            }}
                            onMouseDown={(e) => {
                              e.stopPropagation();
                            }}
                          >
                            {isActive && (
                              <div
                                className="absolute inset-0 rounded-lg animate-pulse"
                                style={{
                                  background: 'radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 70%)',
                                }}
                              />
                            )}
                            {shouldHighlight && isRunning && (
                              <div 
                                className="agent-thinking-particles"
                                style={{ color: categoryColor }}
                              />
                            )}
                            <div
                              className={cn(
                                'w-10 h-10 rounded-full flex items-center justify-center text-xl mx-auto mb-2 transition-all',
                                shouldHighlight && 'scale-110'
                              )}
                              style={{
                                background: shouldHighlight ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                                border: `2px solid ${shouldHighlight ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)'}`,
                              }}
                            >
                              {getAgentIcon(agent.role, actualIndex)}
                            </div>
                            <div className="text-xs font-semibold text-slate-100 truncate">
                              {agent.role}
                            </div>
                            {shouldHighlight && (
                              <div className="text-[10px] text-blue-400 mt-1">
                                {isReplaying || replayIndex !== null ? 'Replaying' : isCompleted ? 'Completed' : 'Active'}
                              </div>
                            )}
                          </div>

                          {isSelected && (
                            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-30">
                              <AgentDetailsPopover
                                agent={agent}
                                agentIndex={actualIndex}
                                categoryColor={categoryColor}
                                nodeEvents={nodeEvents}
                                onClose={() => setSelectedAgentIndex(null)}
                                onEditNode={onEditNode}
                              />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </>
        ) : null}

        {agents.length > MAX_AGENTS_PER_ROOM && (
          <div className="text-center mt-4 text-xs text-slate-500">
            +{agents.length - MAX_AGENTS_PER_ROOM} more agent{agents.length - MAX_AGENTS_PER_ROOM !== 1 ? 's' : ''} (max {MAX_AGENTS_PER_ROOM} shown)
          </div>
        )}
      </div>

      {/* Timeline Scrubber (only show when completed and has messages) */}
      {isCompleted && timelineMessages.length > 0 && (
        <div className="px-4 py-3 border-t border-white/8">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-medium text-slate-300">Conversation Timeline</span>
            <div className="flex items-center gap-1 ml-auto">
              <button
                onClick={handleReplayReset}
                className="p-1 hover:bg-white/10 rounded transition-colors"
                title="Reset timeline"
              >
                <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
              </button>
              <button
                onClick={() => handleReplayStep('back')}
                className="p-1 hover:bg-white/10 rounded transition-colors"
                title="Previous message"
                disabled={replayIndex === null || replayIndex === 0}
              >
                <SkipBack className="w-3.5 h-3.5 text-slate-400" />
              </button>
              <button
                onClick={handleReplayToggle}
                className="p-1.5 hover:bg-white/10 rounded transition-colors"
                title={isReplaying ? 'Pause replay' : 'Play replay'}
              >
                {isReplaying ? (
                  <Pause className="w-4 h-4 text-slate-300" />
                ) : (
                  <Play className="w-4 h-4 text-slate-300" />
                )}
              </button>
              <button
                onClick={() => handleReplayStep('forward')}
                className="p-1 hover:bg-white/10 rounded transition-colors"
                title="Next message"
                disabled={replayIndex === null || (replayIndex !== null && replayIndex >= timelineMessages.length - 1)}
              >
                <SkipForward className="w-3.5 h-3.5 text-slate-400" />
              </button>
            </div>
          </div>
          
          {/* Timeline scrubber */}
          <div className="relative">
            <div className="h-2 bg-white/10 rounded-full overflow-hidden cursor-pointer" onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const x = e.clientX - rect.left;
              const percentage = x / rect.width;
              const index = Math.floor(percentage * timelineMessages.length);
              handleTimelineSeek(Math.max(0, Math.min(index, timelineMessages.length - 1)));
            }}>
              <div
                className="h-full transition-all duration-200 rounded-full"
                style={{
                  width: replayIndex !== null ? `${((replayIndex + 1) / timelineMessages.length) * 100}%` : '0%',
                  background: `linear-gradient(90deg, ${categoryColor}, #f0b429)`,
                }}
              />
            </div>
            {/* Timeline markers */}
            <div className="absolute top-0 left-0 right-0 h-2 flex items-center">
              {timelineMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={cn(
                    'absolute w-1 h-1 rounded-full cursor-pointer transition-all',
                    replayIndex !== null && idx <= replayIndex ? 'bg-white' : 'bg-white/30',
                    msg.agentIndex >= 0 && 'ring-1',
                  )}
                  style={{
                    left: `${((idx + 0.5) / timelineMessages.length) * 100}%`,
                    transform: 'translateX(-50%)',
                    borderColor: msg.agentIndex >= 0 ? categoryColor : undefined,
                  }}
                  title={`Message ${idx + 1}: ${msg.message.substring(0, 50)}...`}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleTimelineSeek(idx);
                  }}
                />
              ))}
            </div>
          </div>
          
          {/* Current message display */}
          {replayIndex !== null && timelineMessages[replayIndex] && (
            <div className="mt-2 p-2 bg-white/5 rounded text-xs text-slate-300 border-l-2" style={{ borderColor: categoryColor }}>
              <div className="flex items-center gap-2 mb-1">
                {timelineMessages[replayIndex].agentIndex >= 0 && (
                  <span className="font-medium text-slate-200">
                    {agents[timelineMessages[replayIndex].agentIndex]?.role || 'System'}:
                  </span>
                )}
                <span className="text-slate-500 text-[10px]">
                  {new Date(timelineMessages[replayIndex].timestamp).toLocaleTimeString()}
                </span>
                <span className="ml-auto text-slate-500">
                  {replayIndex + 1} / {timelineMessages.length}
                </span>
              </div>
              <div className="text-slate-400 line-clamp-2">
                {timelineMessages[replayIndex].message}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Room Analytics - Always show when completed or has events */}
      {(isCompleted || nodeEvents.length > 0) && (
        <div className="px-4 py-3 border-t border-white/8">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs font-medium text-slate-300">Room Analytics</span>
            {nodeEvents.length === 0 && (
              <span className="text-[10px] text-slate-500 ml-auto">No events yet</span>
            )}
            {process.env.NODE_ENV === 'development' && nodeEvents.length > 0 && (
              <span className="text-[10px] text-slate-500 ml-auto">({nodeEvents.length} total events)</span>
            )}
          </div>
          <div className="grid grid-cols-3 gap-2">
            {displayAgents.map((agent, index) => {
              // Get all events for this agent (using agent field directly)
              const agentEvents = nodeEvents.filter(event => {
                // First priority: Use agent field directly from event
                if (event.agent) {
                  const agentName = event.agent.toLowerCase().trim();
                  const role = agent.role.toLowerCase().trim();
                  // More flexible matching: exact match, contains, or word match
                  if (agentName === role) return true;
                  if (agentName.includes(role) || role.includes(agentName)) return true;
                  // Check if any word in the role matches
                  const roleWords = role.split(/\s+/);
                  const agentWords = agentName.split(/\s+/);
                  if (roleWords.some(word => word.length > 3 && agentWords.includes(word))) return true;
                  if (agentWords.some(word => word.length > 3 && roleWords.includes(word))) return true;
                }
                // Fallback: check message content for agent role
                const message = event.message?.toLowerCase() || '';
                const role = agent.role.toLowerCase();
                if (message.includes(role)) return true;
                // Check for partial matches (e.g., "Content Strategist" matches "Content S...")
                const roleWords = role.split(/\s+/);
                return roleWords.some(word => word.length > 3 && message.includes(word));
              });
              
              // Count meaningful events (agent_started, agent_completed, agent_thinking, agent_tool_called, task_started, task_completed)
              const meaningfulEvents = agentEvents.filter(e => 
                ['agent_started', 'agent_completed', 'agent_thinking', 'agent_tool_called', 
                 'agent_output', 'task_started', 'task_completed', 'node_progress'].includes(e.event_type)
              );
              const messageCount = meaningfulEvents.length;
              
              // Calculate time based on task completion events
              const taskEvents = agentEvents.filter(e => e.event_type === 'task_completed' || e.event_type === 'agent_completed');
              const estimatedTime = taskEvents.length > 0 ? taskEvents.length * 15 : messageCount * 2; // 15s per task, 2s per message
              
              // Calculate estimated cost per agent based on event count
              // Distribute total cost proportionally based on meaningful event count
              const totalMeaningfulEvents = nodeEvents.filter(e => 
                ['agent_started', 'agent_completed', 'agent_thinking', 'agent_tool_called', 
                 'agent_output', 'task_started', 'task_completed', 'node_progress'].includes(e.event_type)
              ).length;
              const agentCost = cost && totalMeaningfulEvents > 0 
                ? (cost * messageCount) / totalMeaningfulEvents 
                : 0;
              
              // Calculate token usage for this agent - check multiple locations
              const agentInputTokens = agentEvents.reduce((sum, e) => {
                const tokens = e.input_tokens || 
                              e.data?.input_tokens ||
                              e.data?.tokens_used?.input_tokens || 
                              e.data?.tokens_used?.input ||
                              0;
                return sum + (typeof tokens === 'number' ? tokens : 0);
              }, 0);
              const agentOutputTokens = agentEvents.reduce((sum, e) => {
                const tokens = e.output_tokens || 
                              e.data?.output_tokens ||
                              e.data?.tokens_used?.output_tokens || 
                              e.data?.tokens_used?.output ||
                              0;
                return sum + (typeof tokens === 'number' ? tokens : 0);
              }, 0);
              const agentTotalTokens = agentEvents.reduce((sum, e) => {
                const total = e.total_tokens || 
                             e.data?.total_tokens ||
                             e.data?.tokens_used?.total_tokens || 
                             e.data?.tokens_used?.total ||
                             (agentInputTokens > 0 || agentOutputTokens > 0 ? 
                               (e.input_tokens || e.data?.input_tokens || e.data?.tokens_used?.input_tokens || e.data?.tokens_used?.input || 0) + 
                               (e.output_tokens || e.data?.output_tokens || e.data?.tokens_used?.output_tokens || e.data?.tokens_used?.output || 0) : 
                               0);
                return sum + (typeof total === 'number' ? total : 0);
              }, 0);
              
              // Debug logging (remove in production)
              if (process.env.NODE_ENV === 'development' && index === 0) {
                console.log(`[Room Analytics] Agent: ${agent.role}`, {
                  totalEvents: nodeEvents.length,
                  agentEvents: agentEvents.length,
                  meaningfulEvents: meaningfulEvents.length,
                  messageCount,
                  cost,
                  agentCost,
                  totalMeaningfulEvents,
                  tokens: { input: agentInputTokens, output: agentOutputTokens, total: agentTotalTokens },
                  sampleEvents: agentEvents.slice(0, 3).map(e => ({
                    type: e.event_type,
                    hasTokens: !!(e.input_tokens || e.output_tokens || e.data?.tokens_used),
                    tokens: e.data?.tokens_used,
                  })),
                });
              }
              
              return (
                <div
                  key={index}
                  className="p-2 bg-white/5 rounded-lg border border-white/10"
                >
                  <div className="text-[10px] text-slate-400 mb-1 truncate">{agent.role}</div>
                  <div className="flex items-center gap-1 text-xs text-slate-300 mb-1">
                    <MessageSquare className="w-3 h-3" />
                    <span>{messageCount} {messageCount === 1 ? 'event' : 'events'}</span>
                  </div>
                  {/* Always show token row - display 0 if no tokens */}
                  <div className="flex items-center gap-1 text-xs text-cyan-400 mb-1">
                    <span className="text-[10px]">📊</span>
                    <span className="text-[10px]">
                      {agentTotalTokens > 0 ? (
                        <>
                          {agentInputTokens > 0 && `${agentInputTokens} in`}
                          {agentInputTokens > 0 && agentOutputTokens > 0 && ' / '}
                          {agentOutputTokens > 0 && `${agentOutputTokens} out`}
                          {agentTotalTokens > 0 && agentTotalTokens !== (agentInputTokens + agentOutputTokens) && ` (${agentTotalTokens} total)`}
                        </>
                      ) : (
                        '0 tokens'
                      )}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-amber-400 mb-1">
                    <DollarSign className="w-3 h-3" />
                    <span>${agentCost > 0 ? agentCost.toFixed(4) : '0.0000'}</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-slate-400">
                    <Clock className="w-3 h-3" />
                    <span>~{estimatedTime > 0 ? estimatedTime : 0}s</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Room Footer */}
      <div className="px-4 py-3 border-t border-white/8 flex items-center justify-between">
        {isRunning && (
          <div className="flex-1 mr-4">
            <div className="flex justify-between text-xs text-slate-400 mb-1.5">
              <span>
                {activeAgentIndex !== undefined && displayAgents[activeAgentIndex]
                  ? `${displayAgents[activeAgentIndex].role} working...`
                  : 'Processing...'}
              </span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full transition-all duration-300 rounded-full"
                style={{
                  width: `${progress}%`,
                  background: `linear-gradient(90deg, ${categoryColor}, #f0b429)`,
                  boxShadow: `0 0 3px ${categoryColor}15`, // Much reduced glow
                }}
              />
            </div>
          </div>
        )}

        <div className="flex items-center gap-4 text-xs">
          {cost !== undefined && cost !== null && (
            <div className="flex items-center gap-1 text-slate-400">
              <DollarSign className="w-3.5 h-3.5" />
              <span className="text-amber-400 font-medium">
                ${cost > 0 ? (cost < 0.01 ? cost.toFixed(4) : cost.toFixed(2)) : '0.00'}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3"
        style={{
          backgroundColor: categoryColor,
          border: '2px solid rgba(255, 255, 255, 0.8)',
          boxShadow: `0 0 4px ${categoryColor}15`, // Much reduced glow
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3"
        style={{
          backgroundColor: categoryColor,
          border: '2px solid rgba(255, 255, 255, 0.8)',
          boxShadow: `0 0 4px ${categoryColor}15`, // Much reduced glow
        }}
      />
    </div>
  );
});

AgentRoom.displayName = 'AgentRoom';

