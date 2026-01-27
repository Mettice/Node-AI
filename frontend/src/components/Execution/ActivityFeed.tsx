/**
 * Activity Feed Component - Real-time streaming activity feed
 * 
 * Displays live updates from workflow execution including:
 * - Node start/completion
 * - Agent actions (for CrewAI, LangChain agents)
 * - Progress updates
 * - Tool calls
 * - Logs and errors
 */

import { useEffect, useRef, useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  Clock, 
  Brain, 
  Wrench, 
  Play,
  FileText,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/utils/cn';
import type { StreamEvent } from '@/services/streaming';
import { streamClient } from '@/services/streaming';
import { useExecutionStore } from '@/store/executionStore';

interface ActivityFeedProps {
  executionId: string | null;
  className?: string;
}

interface ActivityItem {
  id: string;
  event: StreamEvent;
  timestamp: Date;
}

const eventIcons: Record<string, any> = {
  node_started: Play,
  node_completed: CheckCircle2,
  node_failed: XCircle,
  node_progress: Loader2,
  agent_started: Brain,
  agent_thinking: Brain,
  agent_tool_called: Wrench,
  agent_output: FileText,
  agent_completed: CheckCircle2,
  task_started: Play,
  task_completed: CheckCircle2,
  log: FileText,
  error: AlertCircle,
};

const eventColors: Record<string, string> = {
  node_started: 'text-blue-400',
  node_completed: 'text-green-400',
  node_failed: 'text-red-400',
  node_progress: 'text-blue-400',
  agent_started: 'text-amber-400',
  agent_thinking: 'text-amber-300',
  agent_tool_called: 'text-yellow-400',
  agent_output: 'text-blue-300',
  agent_completed: 'text-green-400',
  task_started: 'text-blue-400',
  task_completed: 'text-green-400',
  log: 'text-slate-400',
  error: 'text-red-400',
};

export function ActivityFeed({ executionId, className }: ActivityFeedProps) {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const feedEndRef = useRef<HTMLDivElement>(null);
  const activityIdCounter = useRef(0);
  const { addNodeEvent, setCurrentNode } = useExecutionStore();

  const formatEventMessage = (event: StreamEvent): string => {
    const { event_type, data, agent, task } = event;

    switch (event_type) {
      case 'node_started':
        return data.message || `Starting...`;
      case 'node_completed':
        return data.message || `Completed`;
      case 'node_failed':
        return data.message || `Failed`;
      case 'node_progress':
        const progress = data.progress ? Math.round(data.progress * 100) : 0;
        return data.message || `Progress: ${progress}%`;
      case 'agent_started':
        return `🤖 ${agent || 'Agent'} started`;
      case 'agent_thinking':
        return `💭 ${agent || 'Agent'} thinking...`;
      case 'agent_tool_called':
        return `🔧 ${agent || 'Agent'} using tool: ${data.tool || 'unknown'}`;
      case 'agent_output':
        return `✍️ ${agent || 'Agent'} output`;
      case 'agent_completed':
        return `✅ ${agent || 'Agent'} completed`;
      case 'task_started':
        return `📋 Task: ${task || data.task || 'unknown'}`;
      case 'task_completed':
        return `✅ Task completed: ${task || data.task || 'unknown'}`;
      case 'log':
        return data.message || 'Log message';
      case 'error':
        return `❌ Error: ${data.message || 'Unknown error'}`;
      default:
        return data.message || `${event_type}`;
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // Auto-scroll to bottom when new activities arrive
  useEffect(() => {
    if (feedEndRef.current) {
      feedEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [activities]);

  // Connect to stream when executionId changes
  useEffect(() => {
    if (!executionId) {
      setActivities([]);
      return;
    }

    // Connect to stream
    streamClient.connect(executionId);

    // Subscribe to events
    const unsubscribe = streamClient.subscribe((event: StreamEvent) => {
      const activity: ActivityItem = {
        id: `activity-${activityIdCounter.current++}`,
        event,
        timestamp: new Date(event.timestamp),
      };
      
      setActivities((prev) => [...prev, activity]);

      // Update execution store with node events
      if (event.node_id) {
        // Update current node
        if (event.event_type === 'node_started') {
          setCurrentNode(event.node_id);
        } else if (event.event_type === 'node_completed' || event.event_type === 'node_failed') {
          // Clear current node if this node completed
          const currentState = useExecutionStore.getState();
          if (currentState.currentNodeId === event.node_id) {
            setCurrentNode(null);
          }
        }

        // Add event to node's event list
        const message = formatEventMessage(event);
        addNodeEvent(event.node_id, {
          event_type: event.event_type,
          message,
          timestamp: event.timestamp,
          progress: event.data?.progress,
        });
      }
    });

    // Cleanup on unmount
    return () => {
      unsubscribe();
      streamClient.disconnect();
    };
  }, [executionId, addNodeEvent, setCurrentNode]);

  if (!executionId) {
    return (
      <div className={cn('p-4 text-center text-slate-400', className)}>
        <p>No active execution</p>
        <p className="text-sm mt-1">Start a workflow to see live activity</p>
      </div>
    );
  }

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Header */}
      <div className="px-4 py-2 border-b border-white/10 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">Live Activity</h3>
        <div className="flex items-center gap-2">
          <div className={cn(
            'w-2 h-2 rounded-full',
            streamClient.connected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
          )} />
          <span className="text-xs text-slate-400">
            {streamClient.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Activity Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {activities.length === 0 ? (
          <div className="text-center text-slate-400 py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
            <p className="text-sm">Waiting for activity...</p>
          </div>
        ) : (
          activities.map((activity) => {
            const Icon = eventIcons[activity.event.event_type] || Clock;
            const color = eventColors[activity.event.event_type] || 'text-slate-400';
            const isRunning = activity.event.event_type === 'node_progress' || 
                            activity.event.event_type === 'agent_thinking';

            return (
              <div
                key={activity.id}
                className={cn(
                  'flex items-start gap-3 p-2 rounded-lg border border-white/5 bg-white/2',
                  'hover:bg-white/5 transition-colors'
                )}
              >
                <Icon
                  className={cn(
                    'w-4 h-4 mt-0.5 flex-shrink-0',
                    color,
                    isRunning && 'animate-spin'
                  )}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-300">
                      {formatEventMessage(activity.event)}
                    </span>
                    <span className="text-xs text-slate-500 ml-2">
                      {formatTime(activity.timestamp)}
                    </span>
                  </div>
                  
                  {/* Additional details */}
                  {activity.event.data.thought && (
                    <div className="mt-1 text-xs text-slate-400 italic pl-7">
                      "{activity.event.data.thought.substring(0, 100)}..."
                    </div>
                  )}
                  
                  {activity.event.data.progress !== undefined && (
                    <div className="mt-1 pl-7">
                      <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 transition-all duration-300"
                          style={{ width: `${(activity.event.data.progress * 100)}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
        <div ref={feedEndRef} />
      </div>
    </div>
  );
}

