/**
 * Custom node component for React Flow
 */

import { memo, useState, useEffect, useRef, useMemo } from 'react';
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
  CheckCircle,
  XCircle,
  Loader2,
  Clock,
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
  // New icons for AI nodes
  Lightbulb,
  TrendingUp,
  PenTool,
  Code,
  Target,
  BarChart3,
  Shield,
  FileCheck,
  Sparkles,
  PieChart,
  Phone,
  FileEdit,
  UserPlus,
  FileText as FileTextIcon,
  Zap,
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
import { AgentRoom, type Agent } from './AgentRoom';
import { AgentRoomSuggestion } from './AgentRoomSuggestion';

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
  bm25_search: Search, // BM25 text search
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
  // Intelligence nodes
  smart_data_analyzer: BarChart3, // Data analysis
  auto_chart_generator: PieChart, // Chart generation
  content_moderator: Shield, // Content moderation
  meeting_summarizer: FileTextIcon, // Meeting summaries
  lead_scorer: Target, // Lead scoring
  ai_web_search: Search, // AI Web Search
  // Business nodes
  stripe_analytics: DollarSign, // Revenue analytics
  cost_optimizer: TrendingUp, // Cost optimization
  social_analyzer: MessageSquare, // Social media analysis
  ab_test_analyzer: BarChart3, // A/B testing
  // Content nodes
  blog_generator: PenTool, // Blog writing
  brand_generator: Sparkles, // Brand assets
  podcast_transcriber: Mic, // Podcast transcription
  social_scheduler: MessageSquare, // Social scheduling
  // Developer nodes
  bug_triager: Shield, // Bug triaging
  docs_writer: FileText, // Documentation
  performance_monitor: Zap, // Performance monitoring
  security_scanner: Shield, // Security scanning
  // Sales nodes
  call_summarizer: Phone, // Call summaries
  followup_writer: FileEdit, // Follow-up emails
  lead_enricher: UserPlus, // Lead enrichment
  proposal_generator: FileTextIcon, // Proposal generation
};

// Status icon mapping
const statusIcons: Record<string, React.ComponentType<{ className?: string; fill?: string }>> = {
  pending: Clock,
  completed: CheckCircle,
  failed: XCircle,
  running: Loader2,
};

interface CustomNodeData {
  label?: string;
  category?: string;
  status?: NodeStatus;
  config?: Record<string, any>;
}

// Node tier classification based on "Living Intelligence" hierarchy
const NODE_TIER_MAP = {
  // Tier 1 - AI/Intelligence (240-260px)
  llm: 1,
  agent: 1,
  memory: 1,
  intelligence: 1, // AI Intelligence & Analytics nodes
  
  // Tier 2 - Processing (200-240px) 
  processing: 2,
  embedding: 2,
  tool: 2,
  training: 2,
  business: 2, // Business Intelligence nodes
  content: 2, // Content Creation nodes
  developer: 2, // Developer Tools nodes
  sales: 2, // Sales & CRM nodes
  
  // Tier 3 - Input/Output (180-200px)
  input: 3,
  retrieval: 3,
  
  // Tier 4 - Storage/Infrastructure (160-180px)
  storage: 4,
  data: 4,
  communication: 4, // Communication nodes
} as const;

// Tier-specific styling configuration
const TIER_CONFIG = {
  1: {
    minWidth: '190px', // Further reduced after removing edit icon
    maxWidth: '210px',
    hasPersistentGlow: true,
    hasBreathingAnimation: true,
    styleClass: 'tier-1-gradient', // Gradient border style
    iconSize: 'w-10 h-10', // 40px for prominence
  },
  2: {
    minWidth: '160px', // Further reduced after removing edit icon
    maxWidth: '180px',
    hasPersistentGlow: false,
    hasBreathingAnimation: false,
    styleClass: 'tier-2-frosted', // Frosted glass style
    iconSize: 'w-8 h-8', // 32px standard
  },
  3: {
    minWidth: '140px', // Further reduced after removing edit icon
    maxWidth: '160px',
    hasPersistentGlow: false,
    hasBreathingAnimation: false,
    styleClass: 'tier-3-wireframe', // Wireframe style
    iconSize: 'w-6 h-6', // 24px minimal
  },
  4: {
    minWidth: '130px', // Further reduced after removing edit icon
    maxWidth: '150px',
    hasPersistentGlow: false,
    hasBreathingAnimation: false,
    styleClass: 'tier-4-stack', // Stack effect style
    iconSize: 'w-6 h-6', // 24px minimal
  },
} as const;

export const CustomNode = memo(({ data, selected, type, id }: NodeProps<CustomNodeData>) => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [textValue, setTextValue] = useState(data.config?.text || '');
  const [isTextareaFocused, setIsTextareaFocused] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isRoomExpanded, setIsRoomExpanded] = useState(false);
  const [showCompletionAnimation, setShowCompletionAnimation] = useState(false);
  const [hasShownRunning, setHasShownRunning] = useState(false);
  const [showRoomSuggestion, setShowRoomSuggestion] = useState(false);
  const [dismissedRoomSuggestion, setDismissedRoomSuggestion] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const prevStatusForAnimationRef = useRef<string>('idle');
  const nodeRef = useRef<HTMLDivElement>(null);
  const { removeNode, updateNode } = useWorkflowStore();
  const { results, trace, nodeEvents, currentNodeId, nodeStatuses, status: executionStatus } = useExecutionStore();
  
  // Sync textValue with data.config.text when it changes externally
  useEffect(() => {
    const currentText = data.config?.text || '';
    if (currentText !== textValue && !isTextareaFocused) {
      setTextValue(currentText);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data.config, isTextareaFocused]); // textValue intentionally excluded to prevent infinite loop
  
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
  
  // Format node type label - override for specific node types, otherwise use custom label or format the type
  const getNodeTypeLabel = () => {
    // Always override for these specific node types
    if (type === 'crewai_agent') return 'AGENTCREW';
    if (type === 'langchain_agent') return 'AGENTCHAIN';
    
    // Use custom label if provided
    if (data.label) return data.label;
    
    // Default: format type (capitalize and replace underscores)
    return type ? type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ') : 'Node';
  };
  
  const nodeType = getNodeTypeLabel();
  
  // Parse agents for Agent Room visualization (CrewAI only)
  const parseAgents = (): Agent[] => {
    if (type !== 'crewai_agent') return [];
    
    try {
      const agentsConfig = data.config?.agents;
      if (!agentsConfig) return [];
      
      // Handle string or array
      const agents = typeof agentsConfig === 'string' 
        ? JSON.parse(agentsConfig) 
        : agentsConfig;
      
      if (!Array.isArray(agents)) return [];
      
      // Filter out invalid agents and map to Agent type
      return agents
        .filter((agent: any) => agent && agent.role && agent.role.trim())
        .map((agent: any) => ({
          role: agent.role || '',
          goal: agent.goal || '',
          backstory: agent.backstory || '',
        }));
    } catch (error) {
      console.error('Error parsing agents:', error);
      return [];
    }
  };
  
  const agents = parseAgents();
  const shouldShowRoom = type === 'crewai_agent' && agents.length >= 2;
  const canShowRoom = type === 'crewai_agent' && agents.length >= 2;
  
  // Get node position for suggestion popup
  const [nodePosition, setNodePosition] = useState({ x: 0, y: 0 });
  
  // Show suggestion popup if node has 2+ agents but room is not expanded and not dismissed
  useEffect(() => {
    if (canShowRoom && !isRoomExpanded && !dismissedRoomSuggestion && !showRoomSuggestion) {
      // Show suggestion after a short delay
      const timer = setTimeout(() => {
        setShowRoomSuggestion(true);
      }, 2000); // 2 second delay
      return () => clearTimeout(timer);
    }
  }, [canShowRoom, isRoomExpanded, dismissedRoomSuggestion, showRoomSuggestion]);
  
  // Update node position when suggestion should show
  useEffect(() => {
    if (nodeRef.current && showRoomSuggestion) {
      const rect = nodeRef.current.getBoundingClientRect();
      setNodePosition({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      });
    }
  }, [showRoomSuggestion]);
  
  // Calculate node tier and configuration
  // Check both category and type to determine tier
  let nodeTier = NODE_TIER_MAP[category as keyof typeof NODE_TIER_MAP];
  
  // If category doesn't map, check node type directly
  if (!nodeTier) {
    // Tier 1: AI/Intelligence nodes
    if (type === 'chat' || type === 'llm' || type === 'vision' || 
        type === 'langchain_agent' || type === 'crewai_agent' || 
        type === 'memory' || type === 'agent' ||
        // Intelligence category nodes
        type === 'smart_data_analyzer' || type === 'auto_chart_generator' ||
        type === 'content_moderator' || type === 'meeting_summarizer' ||
        type === 'lead_scorer' || type === 'ai_web_search') {
      nodeTier = 1;
    }
    // Tier 2: Processing nodes
    else if (type === 'chunk' || type === 'embed' || type === 'rerank' || 
             type === 'ocr' || type === 'transcribe' || type === 'video_frames' ||
             type === 'advanced_nlp' || type === 'tool' || type === 'finetune' ||
             // Business category nodes
             type === 'stripe_analytics' || type === 'cost_optimizer' ||
             type === 'social_analyzer' || type === 'ab_test_analyzer' ||
             // Content category nodes
             type === 'blog_generator' || type === 'brand_generator' ||
             type === 'podcast_transcriber' || type === 'social_scheduler' ||
             // Developer category nodes
             type === 'bug_triager' || type === 'docs_writer' ||
             type === 'performance_monitor' || type === 'security_scanner' ||
             // Sales category nodes
             type === 'call_summarizer' || type === 'followup_writer' ||
             type === 'lead_enricher' || type === 'proposal_generator') {
      nodeTier = 2;
    }
    // Tier 4: Storage nodes
    else if (type === 'vector_store' || type === 'database' || type === 's3' ||
             type === 'knowledge_graph' || type === 'google_drive' || 
             type === 'google_sheets' || type === 'airtable' ||
             type === 'azure_blob' ||
             // Communication category nodes
             type === 'email' || type === 'slack' || type === 'reddit') {
      nodeTier = 4;
    }
    // Tier 3: Input/Output (default)
    else {
      nodeTier = 3;
    }
  }
  
  const tierConfig = TIER_CONFIG[nodeTier as keyof typeof TIER_CONFIG];
  
  // Check if using fine-tuned model
  const isUsingFinetuned = (type === 'chat' || type === 'embed') && 
    data.config?.use_finetuned_model && 
    data.config?.finetuned_model_id;
  
  // Get category color
  const categoryColor = NODE_CATEGORY_COLORS[category as keyof typeof NODE_CATEGORY_COLORS] || '#9ca3af';
  
  // Auto-expand room when running
  useEffect(() => {
    if (shouldShowRoom && displayStatus === 'running' && !isRoomExpanded) {
      setIsRoomExpanded(true);
    }
  }, [shouldShowRoom, displayStatus, isRoomExpanded]);
  
  // Track completion/failure animations (must be before any early returns)
  useEffect(() => {
    // Track when node starts running
    if (displayStatus === 'running' && !hasShownRunning) {
      setHasShownRunning(true);
    }
    
    // Trigger animation when status changes to completed or failed
    if ((displayStatus === 'completed' || displayStatus === 'failed') && prevStatusForAnimationRef.current !== displayStatus) {
      // Set animation immediately
      setShowCompletionAnimation(true);
      // Reset after animation completes (800ms for the animation duration)
      const timer = setTimeout(() => {
        setShowCompletionAnimation(false);
      }, 800);
      return () => clearTimeout(timer);
    }
    
    // Reset animation flag when status changes away from completed/failed
    if (displayStatus !== 'completed' && displayStatus !== 'failed' && showCompletionAnimation) {
      setShowCompletionAnimation(false);
    }
    
    // Update previous status ref
    prevStatusForAnimationRef.current = displayStatus;
  }, [displayStatus, hasShownRunning, showCompletionAnimation]);
  
  // Get active agent index from execution events (for Agent Room)
  const getActiveAgentIndex = (): number | undefined => {
    if (!shouldShowRoom || displayStatus !== 'running') return undefined;
    
    // Get all events for this node
    const events = nodeEvents[id] || [];
    if (events.length === 0) return undefined;
    
    // Look through recent events (last 10) to find the most recent agent activity
    // Prioritize events with agent field, then fall back to message parsing
    const recentEvents = events.slice(-10).reverse();
    
    for (const event of recentEvents) {
      // First priority: Use agent field directly from event
      if (event.agent) {
        const agentName = event.agent.toLowerCase();
        for (let i = 0; i < agents.length; i++) {
          const role = agents[i].role.toLowerCase();
          if (agentName === role || agentName.includes(role) || role.includes(agentName)) {
            return i;
          }
        }
      }
      
      // Second priority: Check for agent activity event types
      if (['agent_started', 'agent_thinking', 'agent_tool_called', 'agent_output', 'agent_completed', 
           'task_started', 'task_completed'].includes(event.event_type)) {
        // Try to match agent from message if agent field not available
        if (event.message) {
          const message = event.message.toLowerCase();
          for (let i = 0; i < agents.length; i++) {
            const role = agents[i].role.toLowerCase();
            if (message.includes(role)) {
              return i;
            }
          }
        }
      }
      
      // Third priority: Fallback to message content parsing
      if (event.message) {
        const message = event.message.toLowerCase();
        for (let i = 0; i < agents.length; i++) {
          const role = agents[i].role.toLowerCase();
          if (message.includes(role)) {
            return i;
          }
        }
      }
    }
    
    return undefined;
  };
  
  const activeAgentIndex = getActiveAgentIndex();
  
  // Get progress from execution result or events
  const getProgress = (): number => {
    if (displayStatus !== 'running') return 0;
    // Check latest event for progress
    if (latestEvent?.progress !== undefined) return latestEvent.progress;
    // Check displayProgress (from fine-tune or other sources)
    if (displayProgress !== undefined) return displayProgress;
    return 0;
  };
  
  const progress = getProgress();
  
  // Get cost from execution result (use useMemo to prevent object recreation)
  const cost = useMemo(() => executionResult?.cost, [executionResult]);
  
  // Debug: Log cost for Agent Room nodes (only log when cost actually changes)
  const prevCostRef = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (shouldShowRoom && process.env.NODE_ENV === 'development' && cost !== prevCostRef.current) {
      console.log(`[CustomNode] ${id} cost:`, {
        cost,
        hasResult: !!executionResult,
      });
      prevCostRef.current = cost;
    }
  }, [shouldShowRoom, id, cost, executionResult]); // Include executionResult as stable dependency
  
  // Render Agent Room if conditions are met (before regular node rendering)
  if (shouldShowRoom) {
    // Get node events for conversation visualization
    const events = nodeEvents[id] || [];
    
    return (
      <>
        <div ref={nodeRef}>
          <AgentRoom
            agents={agents}
            roomName={data.label || 'Agent Room'}
            isExpanded={isRoomExpanded}
            onToggleExpand={() => {
              setIsRoomExpanded(!isRoomExpanded);
              setShowRoomSuggestion(false);
              setDismissedRoomSuggestion(true);
            }}
            status={displayStatus as 'idle' | 'running' | 'completed' | 'failed'}
            activeAgentIndex={activeAgentIndex}
            progress={progress * 100} // Convert to percentage
            cost={cost}
            categoryColor={categoryColor}
            nodeId={id}
            selected={selected}
            nodeEvents={events}
            onEditNode={() => setShowEditModal(true)}
          />
        </div>
        
        {/* Agent Room Suggestion Popup */}
        {showRoomSuggestion && !isRoomExpanded && (
          <AgentRoomSuggestion
            nodeId={id}
            agentCount={agents.length}
            onConvert={() => {
              setIsRoomExpanded(true);
              setShowRoomSuggestion(false);
              setDismissedRoomSuggestion(true);
            }}
            onDismiss={() => {
              setShowRoomSuggestion(false);
              setDismissedRoomSuggestion(true);
            }}
            position={nodePosition}
            categoryColor={categoryColor}
          />
        )}
        
        {/* Edit Modal for Agent Room */}
        {showEditModal && (
          <NodeEditModal
            node={{ id, type: type || '', data, position: { x: 0, y: 0 } }}
            onClose={() => setShowEditModal(false)}
          />
        )}
      </>
    );
  }
  
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
  } else if (type === 'google_sheets') {
    // Google Sheets nodes use the Google Drive icon from ProviderIcon
    useProviderIcon = true;
    providerIconName = 'googlesheets';
  } else if (type === 'airtable') {
    // Airtable nodes use the Airtable icon from ProviderIcon
    useProviderIcon = true;
    providerIconName = 'airtable';
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
      agent: 'glow-agent',
      memory: 'glow-embedding', // Same as embedding (purple)
      tool: 'glow-processing',  // Same as processing (orange)
      training: 'glow-embedding', // Same as embedding (purple)
      data: 'glow-storage',     // Same as storage (emerald)
    };
    return glowMap[category] || '';
  };

  
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

  // Determine tier-specific classes and styles based on recommendations
  const getTierClass = () => {
    // Tier 1 nodes use the wrapper + inner pattern (no direct class on inner)
    if (nodeTier === 1) return '';
    // Tier 2 uses frosted glass as recommended
    if (nodeTier === 2) return 'node-tier-2-frosted';
    // Tier 3 uses wireframe as recommended  
    if (nodeTier === 3) return 'node-tier-3-wireframe';
    // Tier 4 uses stack effect
    if (nodeTier === 4) return 'node-tier-4-stack';
    // Default fallback
    return 'node-tier-2-frosted';
  };

  // Base node content (used for all tiers)
  const nodeContent = (
    <div
      ref={nodeRef}
      className={cn(
        'cursor-pointer relative overflow-hidden',
        // Apply tier-specific classes - CSS handles all visual styling
        nodeTier === 1 ? 'node-tier-1-inner' : getTierClass(),
        // Tier-specific animations
        tierConfig.hasPersistentGlow && 'node-tier-1-glow',
        tierConfig.hasBreathingAnimation && status === 'idle' && 'node-breathing',
        animationClass,
        isActive && 'node-border-pulse',
        selected && 'ring-2 ring-blue-500 ring-offset-2 ring-offset-slate-900 scale-[1.02] shadow-lg shadow-blue-500/50',
      )}
      style={{
        // NO inline styles - let CSS classes handle everything via !important
        // This ensures nodedesign.html styles apply correctly
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleNodeClick}
      title={type !== 'text_input' ? 'Click to edit' : undefined}
      onMouseDown={(e) => {
        // Don't prevent textarea interaction
        if (type === 'text_input' && (e.target as HTMLElement).closest('textarea')) {
          return;
        }
      }}
      onContextMenu={(e) => {
        // Prevent default browser context menu but allow event to bubble to ReactFlow
        e.preventDefault();
        // Don't stop propagation - let ReactFlow handle it
      }}
    >
      {/* Input handles - matching nodedesign.html */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3"
        style={{ 
          backgroundColor: nodeTier === 3 ? 'transparent' : categoryColor,
          border: `2px solid ${nodeTier === 3 ? categoryColor : 'rgba(255, 255, 255, 0.8)'}`,
          boxShadow: `0 0 10px ${categoryColor}50`,
        }}
      />

      {/* Node header - Clean design matching nodedesign.html */}
      <div
        className="px-3 py-2.5 flex items-center justify-between group relative"
        style={{ 
          // Simple header gradient based on category color
          background: nodeTier === 1 
            ? `linear-gradient(135deg, ${categoryColor}20 0%, ${categoryColor}08 100%)`
            : nodeTier === 2
              ? `linear-gradient(135deg, ${categoryColor}15 0%, ${categoryColor}05 100%)`
              : 'transparent', // Tier 3 & 4: transparent header
          borderBottom: nodeTier === 3 
            ? '1px solid rgba(255, 255, 255, 0.1)' // Wireframe: white border
            : `1px solid ${categoryColor}20`,
        }}
      >
        
        <div className="flex items-center gap-2 relative z-10">
          {/* Icon container - matches nodedesign.html styles */}
          <div 
            className={cn(
              "p-1.5 rounded-lg transition-all duration-300 group-hover:scale-110",
              nodeTier === 3 && "bg-transparent border" // Wireframe style
            )}
            style={{ 
              color: categoryColor,
              background: nodeTier === 3 
                ? 'transparent'
                : `${categoryColor}20`, // Simple background matching nodedesign.html
              borderColor: nodeTier === 3 ? `${categoryColor}80` : undefined,
              boxShadow: `0 0 ${nodeTier === 1 ? '25px' : nodeTier === 2 ? '20px' : '15px'} ${categoryColor}40`,
            }}
          >
            {useProviderIcon ? (
              <ProviderIcon provider={providerIconName} size={nodeTier === 1 ? "lg" : nodeTier === 2 ? "md" : "sm"} />
            ) : (
              Icon && <Icon className={cn(
                tierConfig.iconSize,
                nodeTier === 3 && "stroke-[1.5]" // Thinner stroke for wireframe
              )} />
            )}
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[12px] font-semibold text-slate-100 tracking-[-0.01em] truncate drop-shadow-sm leading-tight">
              {nodeType}
            </span>
            {/* Subtitle: Model or Provider or Type */}
            <span className="text-[10px] text-white/50 font-normal truncate leading-tight">
              {data.config?.model || data.config?.provider || category || 'Node'}
            </span>
          </div>
          
          {isUsingFinetuned && (
            <div className="absolute -top-1 -right-1 bg-amber-500 rounded-full p-0.5" title="Using fine-tuned model">
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
                      className="h-full bg-gradient-to-r from-amber-500 to-amber-400 transition-all duration-300 rounded-full"
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
          {/* Delete button only - Edit is done by clicking the node */}
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
                'rounded-full p-1.5 shadow-lg cursor-pointer transition-all duration-200 hover:scale-110 hover:shadow-xl border border-white/20',
                status === 'completed' && 'bg-green-500 text-white',
                status === 'failed' && 'bg-red-500 text-white',
                status === 'running' && 'bg-blue-500 text-white',
                status === 'pending' && 'bg-amber-500 text-white'
              )}>
                <StatusIcon
                  className={cn(
                    'w-3.5 h-3.5',
                    status === 'running' && 'animate-spin'
                  )}
                  fill={status === 'completed' || status === 'failed' ? "currentColor" : "none"}
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
              <div className="bg-gradient-to-br from-amber-500 to-amber-600 text-black rounded-full p-2 shadow-lg cursor-pointer hover:from-amber-600 hover:to-amber-700 transition-all duration-200 hover:scale-110 hover:shadow-xl border border-white/20">
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

      {/* Node body - show key config or inline text input - Content visible only on hover (except text_input) */}
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
            className="w-full min-h-[80px] px-3 py-2 text-sm text-slate-100 bg-white/8 border border-white/15 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-transparent resize-none placeholder-slate-400 backdrop-blur-sm"
            style={{ fontFamily: 'inherit' }}
          />
        </div>
      ) : (
        <div 
          className={cn(
            "px-3 py-2 transition-all duration-300 ease-out",
            !isHovered && "opacity-0 max-h-0 overflow-hidden",
            isHovered && "opacity-100 max-h-[200px]"
          )}
        >
          <NodeConfigDisplay 
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

      {/* Execution Status Bar (only after node has run) - Show only on hover */}
      {status !== 'idle' && executionResult && (
        <div 
          className={cn(
            "px-3 py-1.5 border-t flex items-center justify-between text-xs transition-all duration-300 ease-out",
            !isHovered && "opacity-0 max-h-0 overflow-hidden border-transparent",
            isHovered && "opacity-100 max-h-[60px]"
          )}
          style={{
            borderTopColor: `${categoryColor}30`,
            background: `linear-gradient(to right, ${categoryColor}12, transparent)`,
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
              <span className="text-amber-400 font-medium">{formatCost(executionResult.cost)}</span>
            )}
          </div>
        </div>
      )}

      {/* Output handles - matching nodedesign.html */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3"
        style={{ 
          backgroundColor: nodeTier === 3 ? 'transparent' : categoryColor,
          border: `2px solid ${nodeTier === 3 ? categoryColor : 'rgba(255, 255, 255, 0.8)'}`,
          boxShadow: `0 0 10px ${categoryColor}50`,
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

  // Wrap Tier 1 nodes with gradient border
  if (nodeTier === 1) {
    return (
      <div className="node-tier-1-wrapper">
        {nodeContent}
      </div>
    );
  }

  // Apply sizing to other tiers (Tier 2, 3, 4) with proper styling
  return nodeContent;
});
CustomNode.displayName = 'CustomNode';