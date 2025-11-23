/**
 * Custom node component for React Flow
 */

import { memo, useState, useEffect, useRef } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import { 
  FileText, 
  Upload,
  Scissors, 
  Brain, 
  Database, 
  Search, 
  MessageSquare,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Pencil,
  Trash2,
  DollarSign,
  BrainCircuit,
  Bot,
  Wrench,
  Users,
  Eye,
  Scan,
  Mic,
  Video,
  Table,
  FileSpreadsheet,
  GraduationCap,
  Cloud,
  Mail,
  Webhook,
  Network,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { NODE_CATEGORY_COLORS } from '@/constants';
import type { NodeStatus } from '@/types/node';
import { NodeEditModal } from './NodeEditModal';
import { NodeConfigDisplay } from './NodeConfigDisplay';
import { useWorkflowStore } from '@/store/workflowStore';
import { useExecutionStore } from '@/store/executionStore';
import { useQuery } from '@tanstack/react-query';
import { getFinetuneStatus } from '@/services/finetune';
import { ProviderIcon } from '@/components/common/ProviderIcon';

// Icon mapping
const nodeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  text_input: FileText,
  file_loader: Upload,
  chunk: Scissors,
  ocr: Scan,
  transcribe: Mic,
  video_frames: Video,
  data_loader: FileSpreadsheet,
  data_to_text: Table,
  embed: Brain,
  vector_store: Database,
  vector_search: Search,
  rerank: Search, // Use Search icon with different styling
  hybrid_retrieval: Search, // Hybrid retrieval combines vector + graph
  knowledge_graph: Network, // Network icon for knowledge graph
  chat: MessageSquare,
  vision: Eye,
  memory: BrainCircuit,
  langchain_agent: Bot, // Will be replaced with ProviderIcon
  tool: Wrench,
  crewai_agent: Users, // Will be replaced with ProviderIcon
  s3: Cloud, // S3 Storage node
  email: Mail, // Email node
  database: Database, // Database node
  slack: MessageSquare, // Slack node
  google_drive: Cloud, // Google Drive node
  reddit: MessageSquare, // Reddit node
  finetune: GraduationCap,
  webhook_input: Webhook, // Webhook Input node
};

// Status icon mapping
const statusIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  pending: Clock,
  completed: CheckCircle2,
  failed: XCircle,
  running: Loader2,
};

interface CustomNodeData {
  label?: string;
  category?: string;
  status?: NodeStatus;
  config?: Record<string, any>;
}

export const CustomNode = memo(({ data, selected, type, id }: NodeProps<CustomNodeData>) => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [textValue, setTextValue] = useState(data.config?.text || '');
  const [isTextareaFocused, setIsTextareaFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { removeNode, updateNode } = useWorkflowStore();
  const { results, trace, nodeEvents, currentNodeId, nodeStatuses, status: executionStatus } = useExecutionStore();
  
  // Sync textValue with data.config.text when it changes externally
  useEffect(() => {
    const currentText = data.config?.text || '';
    if (currentText !== textValue && !isTextareaFocused) {
      setTextValue(currentText);
    }
  }, [data.config?.text, isTextareaFocused, textValue]);
  
  // Get execution status for this node - prioritize real-time status from SSE
  const executionResult = results[id];
  const executionStep = trace && Array.isArray(trace) ? trace.find((step) => step.node_id === id) : undefined;
  
  // Use nodeStatuses (from SSE) first, then fallback to result status, then trace
  // This ensures real-time status from SSE takes priority
  const nodeStatus = nodeStatuses[id] || executionResult?.status || executionStep?.data?.status || (executionStep?.action === 'completed' ? 'completed' : executionStep?.action === 'started' ? 'running' : 'idle') || data.status || 'idle';
  
  // Check if this is the currently active node
  const isActive = currentNodeId === id && (executionStatus === 'running' || executionStatus === 'pending');
  
  // Get latest SSE event for this node
  const latestEvent = nodeEvents[id]?.[nodeEvents[id].length - 1];
  
  // For fine-tune nodes, check job status if we have a job_id
  // Job ID is in the output field of the result
  const jobId = executionResult?.output?.job_id || executionResult?.output?.metadata?.job_id;
  const isFinetuneNode = type === 'finetune';
  
  // Poll fine-tuning job status if node is finetune and has job_id
  const { data: finetuneStatus } = useQuery({
    queryKey: ['finetune-status', jobId],
    queryFn: () => getFinetuneStatus(jobId!),
    enabled: isFinetuneNode && !!jobId && (nodeStatus === 'running' || nodeStatus === 'pending' || nodeStatus === 'idle'),
    refetchInterval: (query) => {
      // Poll every 5 seconds if job is running, every 30 seconds if queued
      const status = query.state.data?.status;
      if (status === 'running' || status === 'queued' || status === 'validating_training_file') {
        return 5000; // 5 seconds
      }
      return false; // Stop polling if completed/failed
    },
  });
  
  // Override status for fine-tune nodes based on job status
  let displayStatus = nodeStatus;
  let displayProgress = latestEvent?.progress;
  if (isFinetuneNode && finetuneStatus) {
    // Map fine-tuning status to node status
    if (finetuneStatus.status === 'succeeded') {
      displayStatus = 'completed';
    } else if (finetuneStatus.status === 'failed' || finetuneStatus.status === 'cancelled') {
      displayStatus = 'failed';
    } else if (finetuneStatus.status === 'running' || finetuneStatus.status === 'queued' || finetuneStatus.status === 'validating_training_file') {
      displayStatus = 'running';
    }
    displayProgress = finetuneStatus.progress;
  }
  
  const category = data.category || type || 'default';
  const status: NodeStatus | 'pending' | 'idle' = displayStatus as any;
  const nodeType = data.label || type || 'Node';
  
  // Check if using fine-tuned model
  const isUsingFinetuned = (type === 'chat' || type === 'embed') && 
    data.config?.use_finetuned_model && 
    data.config?.finetuned_model_id;
  
  // Get category color
  const categoryColor = NODE_CATEGORY_COLORS[category as keyof typeof NODE_CATEGORY_COLORS] || '#9ca3af';
  
  // Get icon - use ProviderIcon for crewai_agent, langchain_agent, vision (based on provider), and s3, otherwise use nodeIcons
  let Icon: React.ComponentType<{ className?: string }> | null = null;
  let useProviderIcon = false;
  let providerIconName = '';
  
  if (type === 'crewai_agent') {
    useProviderIcon = true;
    providerIconName = 'crewai';
  } else if (type === 'langchain_agent') {
    useProviderIcon = true;
    providerIconName = 'langchain';
  } else if (type === 'vision') {
    // For vision nodes, use provider icon if provider is set, otherwise use Eye icon
    const visionProvider = data.config?.provider;
    if (visionProvider) {
      useProviderIcon = true;
      providerIconName = visionProvider;
    } else {
      Icon = nodeIcons[type || ''] || nodeIcons[category] || FileText;
    }
  } else if (type === 's3') {
    // S3 nodes use the S3 icon from ProviderIcon
    useProviderIcon = true;
    providerIconName = 's3';
  } else if (type === 'email') {
    // Email nodes use the Resend icon from ProviderIcon
    useProviderIcon = true;
    providerIconName = 'resend';
  } else if (type === 'slack') {
    // Slack nodes use the Slack icon from ProviderIcon
    useProviderIcon = true;
    providerIconName = 'slack';
  } else if (type === 'google_drive') {
    // Google Drive nodes use the Google Drive icon from ProviderIcon
    useProviderIcon = true;
    providerIconName = 'googledrive';
  } else if (type === 'reddit') {
    // Reddit nodes use the Reddit icon from ProviderIcon
    useProviderIcon = true;
    providerIconName = 'reddit';
  } else {
    Icon = nodeIcons[type || ''] || nodeIcons[category] || FileText;
  }
  
  // Get status icon
  const StatusIcon = (status === 'idle' || !status) ? null : statusIcons[status];
  
  // Format cost
  const formatCost = (cost?: number) => {
    if (!cost || cost === 0) return '$0.00';
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(2)}`;
  };
  
  // Format duration
  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };
  

  // Handle delete
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this node?')) {
      removeNode(id);
    }
  };

  // Handle node click - open edit modal (except for text_input which has inline editing)
  const handleNodeClick = (e: React.MouseEvent) => {
    // Don't handle click if clicking on textarea or its container
    if (type === 'text_input' && (e.target as HTMLElement).closest('textarea')) {
      return;
    }
    e.stopPropagation();
    // Don't open modal for text_input - it has inline editing
    if (type !== 'text_input') {
      setShowEditModal(true);
    }
  };

  // Get glow class based on category
  const getGlowClass = () => {
    const glowMap: Record<string, string> = {
      input: 'glow-input',
      processing: 'glow-processing',
      embedding: 'glow-embedding',
      storage: 'glow-storage',
      retrieval: 'glow-retrieval',
      llm: 'glow-llm',
    };
    return glowMap[category] || '';
  };

  // Track if we should show completion/failure animation
  const [showCompletionAnimation, setShowCompletionAnimation] = useState(false);
  const [hasShownRunning, setHasShownRunning] = useState(false);
  const prevStatusForAnimationRef = useRef<string>(status);
  
  useEffect(() => {
    // Track when node starts running
    if (status === 'running' && !hasShownRunning) {
      setHasShownRunning(true);
    }
    
    // Trigger animation when status changes to completed or failed
    if ((status === 'completed' || status === 'failed') && prevStatusForAnimationRef.current !== status) {
      // Set animation immediately
      setShowCompletionAnimation(true);
      // Reset after animation completes (800ms for the animation duration)
      const timer = setTimeout(() => {
        setShowCompletionAnimation(false);
      }, 800);
      return () => clearTimeout(timer);
    }
    
    // Reset animation flag when status changes away from completed/failed
    if (status !== 'completed' && status !== 'failed' && showCompletionAnimation) {
      setShowCompletionAnimation(false);
    }
    
    prevStatusForAnimationRef.current = status;
  }, [status, hasShownRunning, showCompletionAnimation]);
  
  // Remove debug logging - no longer needed

  // Determine animation classes based on status
  const getAnimationClass = () => {
    // Don't animate if execution is complete
    if (executionStatus === 'completed' || executionStatus === 'failed') {
      return '';
    }
    
    // Active node gets priority animation
    if (isActive && (status === 'running' || status === 'pending')) return 'node-active';
    
    // Running nodes pulse
    if (status === 'running') return 'node-running';
    
    // Pending nodes subtle pulse
    if (status === 'pending') return 'node-pending';
    
    // Completed nodes - animate when transitioning (showCompletionAnimation is set in useEffect)
    if (status === 'completed' && showCompletionAnimation) return 'node-completed';
    
    // Failed nodes - animate when transitioning
    if (status === 'failed' && showCompletionAnimation) return 'node-failed';
    
    return '';
  };
  
  // Get animation class - call it here so it's available for logging
  const animationClass = getAnimationClass();

  return (
    <div
      className={cn(
        'rounded-lg border min-w-[180px] max-w-[240px] cursor-pointer relative',
        'transition-all duration-300 ease-out',
        'hover:scale-[1.03] hover:-translate-y-1 hover:shadow-xl',
        'hover:border-opacity-80',
        selected && 'ring-2 ring-blue-500 scale-[1.02] shadow-lg',
        status !== 'idle' && status !== 'completed' && status !== 'failed' && executionStatus !== 'completed' && executionStatus !== 'failed' && !selected && getGlowClass(),
        animationClass,
        isActive && 'node-border-pulse',
        'node-glass' // Custom glassy style
      )}
      style={{
        background: `rgba(15, 23, 42, 0.35)`, // More transparent dark background
        backdropFilter: 'blur(24px) saturate(180%)',
        WebkitBackdropFilter: 'blur(24px) saturate(180%)',
        borderColor: selected 
          ? 'rgba(59, 130, 246, 0.5)'  // More transparent selection border
          : isActive
            ? `${categoryColor}60`  // More transparent when active
            : (status === 'idle' || !status) 
              ? `${categoryColor}25`  // Very subtle border for idle
              : status === 'completed'
                ? 'rgba(22, 163, 74, 0.4)'  // Subtle green
                : status === 'failed'
                  ? 'rgba(239, 68, 68, 0.5)'  // Subtle red
                  : `${categoryColor}40`,  // More transparent default
        borderWidth: selected || status !== 'idle' ? '1.5px' : '1px',
        color: isActive ? categoryColor : undefined,
        boxShadow: selected 
          ? `0 8px 32px rgba(59, 130, 246, 0.2), 0 0 0 1px ${categoryColor}15, inset 0 1px 0 rgba(255, 255, 255, 0.1)`
          : isActive
            ? `0 4px 20px ${categoryColor}20, 0 2px 8px ${categoryColor}15, inset 0 1px 0 rgba(255, 255, 255, 0.08)`
            : `0 4px 16px rgba(0, 0, 0, 0.2), 0 1px 4px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.06)`,
      }}
      onClick={handleNodeClick}
      onMouseDown={(e) => {
        // Don't prevent textarea interaction
        if (type === 'text_input' && (e.target as HTMLElement).closest('textarea')) {
          return;
        }
      }}
    >
      {/* Input handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3.5 h-3.5 border-2 border-white"
        style={{ 
          backgroundColor: categoryColor,
          boxShadow: `0 2px 4px ${categoryColor}40`
        }}
      />

      {/* Node header */}
      <div
        className="px-3 py-2 rounded-t-lg flex items-center justify-between group relative overflow-hidden transition-all duration-200"
        style={{ 
          background: `linear-gradient(135deg, ${categoryColor}20 0%, ${categoryColor}10 100%)`,
          borderBottom: `1px solid ${categoryColor}25`,
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
        }}
      >
        {/* Subtle pattern overlay */}
        <div className="absolute inset-0 opacity-5" style={{
          backgroundImage: `radial-gradient(circle at 2px 2px, ${categoryColor} 1px, transparent 0)`,
          backgroundSize: '16px 16px'
        }}></div>
        
        <div className="flex items-center gap-1.5 relative z-10">
          <div 
            className="p-1 rounded-md transition-all duration-300 group-hover:scale-110 group-hover:rotate-3"
            style={{ 
              color: categoryColor,
              background: `linear-gradient(135deg, ${categoryColor}30 0%, ${categoryColor}20 100%)`,
              boxShadow: `
                0 2px 4px -1px ${categoryColor}30,
                0 1px 2px -1px ${categoryColor}20,
                inset 0 1px 0 0 rgba(255, 255, 255, 0.4)
              `
            }}
          >
            {useProviderIcon ? (
              <ProviderIcon provider={providerIconName} size="sm" />
            ) : (
              Icon && <Icon className="w-3 h-3" />
            )}
          </div>
          <span className="text-[10px] font-semibold text-slate-100 tracking-tight truncate drop-shadow-sm">{nodeType}</span>
          {isUsingFinetuned && (
            <div className="absolute -top-1 -right-1 bg-purple-500 rounded-full p-0.5" title="Using fine-tuned model">
              <GraduationCap className="w-2.5 h-2.5 text-white" />
            </div>
          )}
        </div>
        
        {/* SSE Event Badge - Show latest event message */}
        {(latestEvent || (isFinetuneNode && finetuneStatus)) && (status === 'running' || status === 'pending') && (
          <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 z-30 pointer-events-none">
            <div className="glass-light rounded-md px-4 py-2.5 text-xs text-slate-200 whitespace-nowrap border border-white/20 shadow-xl backdrop-blur-sm min-w-[180px]">
              <div className="flex items-center gap-1.5 justify-center">
                {status === 'running' && <Loader2 className="w-3 h-3 animate-spin text-blue-400 flex-shrink-0" />}
                <span className="max-w-[160px] truncate font-medium">
                  {isFinetuneNode && finetuneStatus
                    ? finetuneStatus.status === 'validating_training_file'
                      ? 'Validating data...'
                      : finetuneStatus.status === 'queued'
                      ? 'Queued for training...'
                      : finetuneStatus.status === 'running'
                      ? 'Training in progress...'
                      : latestEvent?.message || 'Processing...'
                    : latestEvent?.message || 'Processing...'}
                </span>
              </div>
              {/* Progress bar */}
              {((displayProgress !== undefined && displayProgress > 0) || (isFinetuneNode && finetuneStatus?.progress)) && (
                <div className="mt-1.5 space-y-1">
                  <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-purple-500 to-purple-400 transition-all duration-300 rounded-full"
                      style={{ 
                        width: `${Math.min((finetuneStatus?.progress || displayProgress || 0) * 100, 100)}%` 
                      }}
                    />
                  </div>
                  {isFinetuneNode && finetuneStatus?.progress && (
                    <div className="text-[10px] text-slate-400 text-center">
                      {Math.round(finetuneStatus.progress * 100)}% complete
                      {finetuneStatus.estimated_cost && (
                        <span className="ml-2">• ${finetuneStatus.estimated_cost.toFixed(2)}</span>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
            {/* Arrow pointing to node */}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-transparent border-t-white/20"></div>
          </div>
        )}
        <div className="flex items-center gap-1 relative z-10">
          {/* Hide edit button for text_input - it has inline editing */}
          {type !== 'text_input' && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowEditModal(true);
              }}
              className="opacity-0 group-hover:opacity-100 transition-all duration-200 p-1 hover:bg-white/10 rounded hover:scale-110"
              title="Edit node"
            >
              <Pencil className="w-3 h-3 text-slate-300" />
            </button>
          )}
          <button
            onClick={handleDelete}
            className="opacity-0 group-hover:opacity-100 transition-all duration-200 p-1 hover:bg-red-50 rounded hover:scale-110"
            title="Delete node"
          >
            <Trash2 className="w-3 h-3 text-red-400" />
          </button>
        </div>
        
        {/* Status Badge - Top Left Corner */}
        {StatusIcon && (
          <div className="absolute -top-2 -left-2 group/status z-20">
            <div className="relative">
              <div className={cn(
                'rounded-full p-2 shadow-lg cursor-pointer transition-all duration-200 hover:scale-110 hover:shadow-xl border-2 border-white',
                status === 'completed' && 'bg-gradient-to-br from-green-700 to-green-800 text-white',
                status === 'failed' && 'bg-gradient-to-br from-red-500 to-red-600 text-white',
                status === 'running' && 'bg-gradient-to-br from-blue-500 to-blue-600 text-white',
                status === 'pending' && 'bg-gradient-to-br from-yellow-500 to-yellow-600 text-white'
              )}>
                <StatusIcon
                  className={cn(
                    'w-3.5 h-3.5',
                    status === 'running' && 'animate-spin'
                  )}
                />
              </div>
              {/* Tooltip on hover */}
              <div className="absolute left-0 top-full mt-2 opacity-0 group-hover/status:opacity-100 pointer-events-none transition-all duration-200 z-50 transform translate-y-1 group-hover/status:translate-y-0">
                <div className="bg-gray-900 text-white text-sm rounded-lg px-4 py-2.5 shadow-2xl whitespace-nowrap backdrop-blur-sm min-w-[180px]">
                  <div className="font-semibold mb-1.5 flex items-center gap-1.5">
                    <StatusIcon className={cn('w-3 h-3', status === 'running' && 'animate-spin')} />
                    {status.toUpperCase()}
                  </div>
                  {executionResult?.duration_ms && (
                    <div className="text-gray-300 text-[10px]">Duration: {formatDuration(executionResult.duration_ms)}</div>
                  )}
                  {/* Arrow */}
                  <div className="absolute -top-1 left-3 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Cost Badge - Top Right Corner */}
        {(category === 'llm' || category === 'embedding') && 
         executionResult?.cost !== undefined && 
         executionResult.cost > 0 && (
          <div className="absolute -top-2 -right-2 group/cost z-20">
            <div className="relative">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-full p-2 shadow-lg cursor-pointer hover:from-blue-600 hover:to-blue-700 transition-all duration-200 hover:scale-110 hover:shadow-xl border-2 border-white">
                <DollarSign className="w-3.5 h-3.5" />
              </div>
              {/* Enhanced Tooltip on hover - shows cost and execution details */}
              <div className="absolute right-0 top-full mt-2 opacity-0 group-hover/cost:opacity-100 pointer-events-none transition-all duration-200 z-50 transform translate-y-1 group-hover/cost:translate-y-0">
                <div className="bg-gray-900 text-white text-sm rounded-lg px-4 py-3 shadow-2xl backdrop-blur-sm min-w-[200px]">
                  <div className="font-semibold mb-2 flex items-center gap-1.5 border-b border-gray-700 pb-1.5">
                    <DollarSign className="w-3 h-3" />
                    Cost: {formatCost(executionResult.cost)}
                  </div>
                  {executionResult?.duration_ms && (
                    <div className="text-gray-300 text-[10px] mb-1">Duration: {formatDuration(executionResult.duration_ms)}</div>
                  )}
                  {executionResult?.status && (
                    <div className="text-gray-300 text-[10px]">Status: {executionResult.status}</div>
                  )}
                  {/* Arrow */}
                  <div className="absolute -top-1 right-3 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Node body - show key config or inline text input */}
      {type === 'text_input' ? (
        <div 
          className="px-3 py-2"
          onClick={(e) => e.stopPropagation()}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <textarea
            ref={textareaRef}
            value={textValue}
            onChange={(e) => {
              const newValue = e.target.value;
              setTextValue(newValue);
              // Update store immediately
              updateNode(id, {
                data: {
                  ...data,
                  config: {
                    ...(data.config || {}),
                    text: newValue,
                  },
                },
              });
            }}
            onFocus={(e) => {
              e.stopPropagation();
              setIsTextareaFocused(true);
            }}
            onBlur={(e) => {
              e.stopPropagation();
              setIsTextareaFocused(false);
            }}
            onClick={(e) => {
              e.stopPropagation();
            }}
            onMouseDown={(e) => {
              e.stopPropagation();
              e.preventDefault(); // Prevent React Flow from starting drag
            }}
            onKeyDown={(e) => {
              e.stopPropagation();
            }}
            onKeyUp={(e) => {
              e.stopPropagation();
            }}
            placeholder="Type your text here..."
            className="w-full min-h-[80px] px-3 py-2 text-sm text-slate-100 bg-white/8 border border-white/15 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent resize-none placeholder-slate-400 backdrop-blur-sm"
            style={{ fontFamily: 'inherit' }}
          />
        </div>
      ) : (
        <div className="px-3 py-2">
          <NodeConfigDisplay 
            key={`${id}-${JSON.stringify(data.config || {})}`}
            type={type || ''} 
            config={data.config || {}} 
          />
        </div>
      )}

      {/* Real-time Progress Message (during execution) */}
      {status === 'running' && latestEvent?.message && (
        <div 
          className="px-3 py-2 border-t text-xs"
          style={{
            borderTopColor: `${categoryColor}20`,
            background: `linear-gradient(to right, ${categoryColor}10, transparent)`,
            backdropFilter: 'blur(4px)',
            WebkitBackdropFilter: 'blur(4px)',
          }}
        >
          <div className="flex items-center gap-2 text-blue-300">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            <span className="truncate">{latestEvent.message}</span>
          </div>
        </div>
      )}

      {/* Execution Status Bar (only after node has run) */}
      {status !== 'idle' && executionResult && (
        <div 
          className="px-3 py-1.5 border-t flex items-center justify-between text-xs"
          style={{
            borderTopColor: `${categoryColor}20`,
            background: `linear-gradient(to right, ${categoryColor}08, transparent)`,
            backdropFilter: 'blur(4px)',
            WebkitBackdropFilter: 'blur(4px)',
          }}
        >
          <div className="flex items-center gap-1.5">
            {StatusIcon && (
              <StatusIcon 
                className={cn(
                  'w-3 h-3',
                  status === 'completed' && 'text-green-600',
                  status === 'failed' && 'text-red-400',
                  status === 'running' && 'text-blue-400 animate-spin',
                  status === 'pending' && 'text-yellow-400'
                )}
              />
            )}
            <span className={cn(
              'font-medium',
              status === 'completed' && 'text-green-600',
              status === 'failed' && 'text-red-400',
              status === 'running' && 'text-blue-400',
              status === 'pending' && 'text-yellow-400'
            )}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
          </div>
          <div className="flex items-center gap-2 text-slate-400">
            {executionResult.duration_ms && (
              <span>{formatDuration(executionResult.duration_ms)}</span>
            )}
            {executionResult.cost !== undefined && executionResult.cost > 0 && (
              <span className="text-blue-400 font-medium">{formatCost(executionResult.cost)}</span>
            )}
          </div>
        </div>
      )}

      {/* Output handles */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3.5 h-3.5 border-2 border-white"
        style={{ 
          backgroundColor: categoryColor,
          boxShadow: `0 2px 4px ${categoryColor}40`
        }}
      />

      {/* Edit Modal */}
      {showEditModal && (
        <NodeEditModal
          node={{ id, type: type || '', data, position: { x: 0, y: 0 } }}
          onClose={() => setShowEditModal(false)}
        />
      )}

    </div>
  );
});
CustomNode.displayName = 'CustomNode';


