/**
 * Enhanced Custom Edge Component - "Living Intelligence" Data Flow
 * 
 * Features:
 * - Connection type visualization (solid, dashed, dotted, double)
 * - Data preview on hover tooltips
 * - Connection labels with data type indicators
 * - Animated direction arrows
 * - Flowing particle animation for active data transfer
 * - Glow effects based on execution state
 * - Smooth bezier curves with status-based coloring
 */

import { memo, useMemo, useState } from 'react';
import { getBezierPath } from 'reactflow';
import type { EdgeProps } from 'reactflow';
import { cn } from '@/utils/cn';
import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { NODE_CATEGORY_COLORS } from '@/constants';
import { FileText, Database, Zap, Binary, Type, Hash, Users } from 'lucide-react';

// Data type detection and styling - Distinct colors and styles
const DATA_TYPE_CONFIG = {
  text: {
    style: 'solid',
    color: '#06b6d4', // Bright cyan - Text/String
    icon: Type,
    label: 'Text/String',
    dashArray: 'none',
    strokeWidth: 2,
    idleOpacity: '90', // More visible when idle
  },
  vector: {
    style: 'dashed',
    color: '#8b5cf6', // Vibrant purple - Vector/Embedding
    icon: Binary,
    label: 'Vector/Embedding',
    dashArray: '10 5', // Longer dashes for better visibility
    strokeWidth: 2,
    idleOpacity: '85',
  },
  control: {
    style: 'dotted',
    color: '#f59e0b', // Amber - Control Flow
    icon: Zap,
    label: 'Control Flow',
    dashArray: '3 5', // Dotted pattern
    strokeWidth: 2.5, // Slightly thicker for visibility
    idleOpacity: '80',
  },
  file: {
    style: 'double',
    color: '#10b981', // Emerald green - Large Data/Files
    icon: FileText,
    label: 'Large Data/Files',
    dashArray: 'none',
    strokeWidth: 2,
    idleOpacity: '85',
  },
  data: {
    style: 'solid',
    color: '#ec4899', // Bright pink - Structured Data
    icon: Database,
    label: 'Structured Data',
    dashArray: 'none',
    strokeWidth: 2,
    idleOpacity: '80',
  },
  number: {
    style: 'solid',
    color: '#f97316', // Bright orange - Numeric
    icon: Hash,
    label: 'Numeric',
    dashArray: 'none',
    strokeWidth: 2,
    idleOpacity: '80',
  },
};

// Detect data type from connection context
const detectDataType = (sourceType: string, targetType: string, results: any, source: string): keyof typeof DATA_TYPE_CONFIG => {
  const sourceResult = results[source];
  
  // Check output content to infer data type
  if (sourceResult?.output) {
    const output = sourceResult.output;
    
    // Vector/embedding detection
    if (sourceType === 'embed' || targetType === 'vector_store' || targetType === 'vector_search') {
      return 'vector';
    }
    
    // File/large data detection
    if (sourceType === 'file_loader' || targetType === 'file_loader' || 
        (typeof output === 'object' && (output.chunks || output.documents || output.files))) {
      return 'file';
    }
    
    // Control flow detection
    if (sourceType === 'condition' || targetType === 'condition' || sourceType.includes('control')) {
      return 'control';
    }
    
    // Text detection
    if (typeof output === 'string' || (output.output && typeof output.output === 'string')) {
      return 'text';
    }
    
    // Numeric detection
    if (typeof output === 'number' || (output.tokens_used || output.cost || output.duration_ms)) {
      return 'number';
    }
    
    // Structured data (objects, arrays)
    if (typeof output === 'object') {
      return 'data';
    }
  }
  
  // Fallback based on node types
  if (sourceType === 'llm' || sourceType === 'chat' || targetType === 'llm' || targetType === 'chat') {
    return 'text';
  }
  
  return 'data'; // Default
};

// Generate data preview from results
const generateDataPreview = (results: any, source: string, target: string): string => {
  const sourceResult = results[source];
  if (!sourceResult?.output) return 'No data';
  
  const output = sourceResult.output;
  
  if (typeof output === 'string') {
    const preview = output.length > 50 ? output.substring(0, 47) + '...' : output;
    return `"${preview}"`;
  }
  
  if (output.output && typeof output.output === 'string') {
    const preview = output.output.length > 50 ? output.output.substring(0, 47) + '...' : output.output;
    return `"${preview}"`;
  }
  
  if (output.chunks) {
    return `${output.chunks.length} chunks`;
  }
  
  if (output.documents) {
    return `${output.documents.length} documents`;
  }
  
  if (output.tokens_used) {
    return `${output.tokens_used.total} tokens`;
  }
  
  if (Array.isArray(output)) {
    return `Array[${output.length}]`;
  }
  
  if (typeof output === 'object') {
    const keys = Object.keys(output);
    return `{${keys.slice(0, 2).join(', ')}${keys.length > 2 ? '...' : ''}}`;
  }
  
  return JSON.stringify(output).substring(0, 50) + '...';
};

export const CustomEdge = memo(({
  id,
  source,
  target,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  selected,
  data,
}: EdgeProps) => {
  const [isHovered, setIsHovered] = useState(false);
  // Generate smooth bezier path
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Get execution state from store
  const { results, currentNodeId, nodeStatuses, status: executionStatus } = useExecutionStore();
  const { nodes } = useWorkflowStore();
  
  // Get node information
  const sourceNode = nodes.find(n => n.id === source);
  const targetNode = nodes.find(n => n.id === target);
  const sourceType = sourceNode?.type || 'unknown';
  const targetType = targetNode?.type || 'unknown';
  
  // Get source node category color for edge animation
  const sourceCategory = sourceNode?.data?.category || sourceNode?.type || 'default';
  const sourceCategoryColor = NODE_CATEGORY_COLORS[sourceCategory as keyof typeof NODE_CATEGORY_COLORS] || '#60a5fa';
  
  // Check if both nodes are Agent Rooms (crewai_agent with 2+ agents)
  const isRoomToRoom = useMemo(() => {
    if (sourceType !== 'crewai_agent' || targetType !== 'crewai_agent') return false;
    const sourceAgents = sourceNode?.data?.config?.agents || [];
    const targetAgents = targetNode?.data?.config?.agents || [];
    return sourceAgents.length >= 2 && targetAgents.length >= 2;
  }, [sourceType, targetType, sourceNode?.data?.config?.agents, targetNode?.data?.config?.agents]);
  
  // Determine node statuses
  const sourceStatusRaw = nodeStatuses[source] || results[source]?.status;
  const targetStatusRaw = nodeStatuses[target] || results[target]?.status;
  const sourceStatus: 'idle' | 'pending' | 'running' | 'completed' | 'failed' = 
    (sourceStatusRaw as 'idle' | 'pending' | 'running' | 'completed' | 'failed') || 'idle';
  const targetStatus: 'idle' | 'pending' | 'running' | 'completed' | 'failed' = 
    (targetStatusRaw as 'idle' | 'pending' | 'running' | 'completed' | 'failed') || 'idle';
  
  // Detect data type and get configuration
  const dataType = detectDataType(sourceType, targetType, results, source);
  const typeConfig = DATA_TYPE_CONFIG[dataType];
  
  // Generate data preview for tooltip
  const dataPreview = generateDataPreview(results, source, target);
  
  // Determine edge state
  // Show flow when source completed and target is about to run or is running
  const isFlowing = sourceStatus === 'completed' && 
    (targetStatus === 'running' || targetStatus === 'pending' || currentNodeId === target);
  // Show active state when either node is running
  const isActive = sourceStatus === 'running' || targetStatus === 'running';
  // Show completed when both are done
  const isCompleted = sourceStatus === 'completed' && targetStatus === 'completed';
  // Show pending when target is waiting for source (even if source completed quickly)
  const isPending = targetStatus === 'pending' && (sourceStatus === 'running' || sourceStatus === 'completed');
  // Show flow animation when source has results (completed) and target is pending/running
  // This handles fast nodes that complete before status updates propagate
  const hasSourceResult = !!results[source]?.output;
  const hasTargetResult = !!results[target]?.output;
  const isExecutionRunning = executionStatus === 'running';
  const isFastFlow = hasSourceResult && isExecutionRunning && 
    (targetStatus === 'pending' || targetStatus === 'running' || currentNodeId === target || !hasTargetResult);
  // Show idle when both are idle
  const isIdle = sourceStatus === 'idle' && targetStatus === 'idle';


  // Generate particles for flowing animation
  // SIMPLIFIED: Show particles on ALL edges when execution is running or pending
  // This provides clear visual feedback that the workflow is executing
  const particles = useMemo(() => {
    // Show particles when execution is running OR pending (immediate feedback)
    // This works for all node types and handles fast-completing nodes
    const shouldShowParticles = isExecutionRunning || executionStatus === 'pending';
    
    if (!shouldShowParticles) return [];
    
    // More particles for better visibility - 5 particles with staggered timing
    return [
      { id: 0, delay: '0s' },
      { id: 1, delay: '2.4s' },
      { id: 2, delay: '4.8s' },
      { id: 3, delay: '7.2s' },
      { id: 4, delay: '9.6s' },
    ];
  }, [isExecutionRunning, executionStatus]);

  // Edge color based on state and data type - More distinct colors, special color for room-to-room
  const edgeColor = useMemo(() => {
    // Special purple/violet color for room-to-room connections
    if (isRoomToRoom) {
      if (isCompleted) return '#22c55e';  // Green for completed
      if (isFlowing || isActive) return '#a78bfa';  // Bright violet for active room connections
      if (isPending) return '#c084fc';  // Lighter violet for pending
      if (selected) return '#a78bfa';  // Full violet when selected
      return '#8b5cf6';  // Base violet for idle room connections
    }
    // Standard edge colors
    if (isCompleted) return '#22c55e';  // Green for completed
    if (isFlowing || isActive) return typeConfig.color;  // Full data type color when active
    if (isPending) return '#fbbf24';  // Amber for pending
    if (selected) return typeConfig.color;  // Full color when selected
    // Use data type specific opacity for idle state to maintain distinction
    return typeConfig.color + typeConfig.idleOpacity;  // Data type color with type-specific opacity when idle
  }, [isCompleted, isFlowing, isActive, isPending, selected, typeConfig.color, typeConfig.idleOpacity, isRoomToRoom]);

  // Glow color for active states - Enhanced for room-to-room
  const glowColor = useMemo(() => {
    if (isRoomToRoom) {
      if (isCompleted) return 'rgba(34, 197, 94, 0.6)';
      if (isFlowing || isActive) return 'rgba(167, 139, 250, 0.8)';  // Stronger violet glow for room connections
      if (isPending) return 'rgba(192, 132, 252, 0.5)';
      if (selected) return 'rgba(167, 139, 250, 0.7)';
      return 'rgba(139, 92, 246, 0.4)';  // Base violet glow for idle room connections
    }
    if (isCompleted) return 'rgba(34, 197, 94, 0.5)';
    if (isFlowing || isActive) return 'rgba(59, 130, 246, 0.6)';
    if (isPending) return 'rgba(251, 191, 36, 0.4)';
    if (selected) return 'rgba(167, 139, 250, 0.6)'; // Purple glow for selected
    return 'transparent';
  }, [isCompleted, isFlowing, isActive, isPending, selected, isRoomToRoom]);

  // Edge stroke width - Use data type specific width, thicker for room-to-room
  const strokeWidth = useMemo(() => {
    const baseWidth = isRoomToRoom ? (typeConfig.strokeWidth || 2) + 1.5 : (typeConfig.strokeWidth || 2);
    if (selected) return baseWidth + 1;
    if (isFlowing || isActive) return baseWidth + 0.5;
    if (isCompleted) return baseWidth;
    return baseWidth - 0.5; // Slightly thinner when idle
  }, [selected, isFlowing, isActive, isCompleted, typeConfig.strokeWidth, isRoomToRoom]);

  // Create unique path ID for this edge
  const pathId = `edge-path-${id.replace(/[^a-zA-Z0-9]/g, '_')}`;

  // Calculate midpoint for label and arrow placement
  const midX = (sourceX + targetX) / 2;
  const midY = (sourceY + targetY) / 2;
  
  // Calculate direction vector for arrow
  const dx = targetX - sourceX;
  const dy = targetY - sourceY;
  const length = Math.sqrt(dx * dx + dy * dy);
  const unitX = dx / length;
  const unitY = dy / length;

  return (
    <g className="react-flow__edge-group">
      {/* SVG Definitions for gradients and filters */}
      <defs>
        {/* Data type specific gradient */}
        <linearGradient id={`connectionGradient-${pathId}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={typeConfig.color + '60'} />
          <stop offset="100%" stopColor={typeConfig.color + '30'} />
        </linearGradient>
        {/* Active connection gradient */}
        <linearGradient id={`activeConnectionGradient-${pathId}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={typeConfig.color} />
          <stop offset="100%" stopColor={typeConfig.color + 'CC'} />
        </linearGradient>
        <filter id={`glow-${pathId}`}>
          <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
          <feMerge> 
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        {/* Arrow marker for flowing arrows */}
        <marker
          id={`arrowhead-${pathId}`}
          markerWidth="8"
          markerHeight="8"
          refX="7"
          refY="4"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <polygon
            points="0 0, 8 4, 0 8"
            fill={typeConfig.color}
            opacity="0.9"
            style={{
              filter: `drop-shadow(0 0 2px ${typeConfig.color})`,
            }}
          />
        </marker>
      </defs>

      {/* Hidden path for particle animation */}
      <path
        id={pathId}
        d={edgePath}
        fill="none"
        stroke="none"
        strokeWidth="0"
      />

      {/* Glow layer - behind main edge - Data type specific glow */}
      {(isFlowing || isActive || isPending) && (
        <path
          d={edgePath}
          fill="none"
          stroke={typeConfig.color}
          strokeWidth={strokeWidth + 2}
          strokeLinecap="round"
          strokeDasharray={typeConfig.dashArray}
          strokeOpacity="0.4"
          className="transition-all duration-500"
          style={{ filter: `blur(4px)` }}
        />
      )}


      {/* Double line effect for file data type - More visible parallel lines */}
      {typeConfig.style === 'double' && (
        <>
          {/* Bottom line - thicker, slightly offset */}
          <path
            d={edgePath}
            fill="none"
            stroke={edgeColor}
            strokeWidth={strokeWidth + 1}
            strokeOpacity="0.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="connection-double-line"
            style={{ 
              filter: `drop-shadow(0 2px 2px ${typeConfig.color}40)`,
            }}
          />
          {/* Top line - main line */}
          <path
            d={edgePath}
            fill="none"
            stroke={edgeColor}
            strokeWidth={strokeWidth}
            strokeOpacity="1"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="connection-double-line"
            style={{ 
              filter: `drop-shadow(0 0 3px ${typeConfig.color}60)`,
            }}
          />
        </>
      )}

      {/* Main edge path */}
      {typeConfig.style !== 'double' && (
        <path
          d={edgePath}
          fill="none"
          stroke={
            isFlowing || isActive || isPending 
              ? `url(#activeConnectionGradient-${pathId})` 
              : `url(#connectionGradient-${pathId})`
          }
          strokeWidth={strokeWidth}
          strokeOpacity="1"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={isRoomToRoom ? 'none' : typeConfig.dashArray}
          className={`edge-${dataType} transition-all duration-300 ${isRoomToRoom ? 'room-connection' : ''}`}
          style={{
            // Enhanced glow for room-to-room connections
            filter: isRoomToRoom 
              ? (isFlowing || isActive) 
                ? `drop-shadow(0 0 6px ${edgeColor}80) drop-shadow(0 0 3px ${edgeColor}60)` 
                : `drop-shadow(0 0 3px ${edgeColor}40)`
              : (isFlowing || isActive) 
                ? `drop-shadow(0 0 3px ${typeConfig.color}60)` 
                : 'none',
          }}
        />
      )}

      {/* Connection label with data type icon */}
      {(isHovered || selected || isFlowing || isRoomToRoom) && (
        <g transform={`translate(${midX}, ${midY})`}>
          {/* Label background */}
          <rect
            x={isRoomToRoom ? "-35" : "-30"}
            y="-10"
            width={isRoomToRoom ? "70" : "60"}
            height="20"
            rx="10"
            fill={isRoomToRoom ? "rgba(139, 92, 246, 0.9)" : "rgba(0, 0, 0, 0.8)"}
            stroke={isRoomToRoom ? "#a78bfa" : typeConfig.color}
            strokeWidth={isRoomToRoom ? "2" : "1"}
            strokeOpacity="0.8"
          />
          
          {/* Room-to-room icon or data type icon */}
          {isRoomToRoom ? (
            <foreignObject x="-8" y="-6" width="16" height="12">
              <Users 
                className="w-3 h-3 text-white connection-label-icon" 
                style={{ color: '#fff' }}
              />
            </foreignObject>
          ) : (
            <foreignObject x="-8" y="-6" width="16" height="12">
              <typeConfig.icon 
                className="w-3 h-3 text-white connection-label-icon" 
                style={{ color: typeConfig.color }}
              />
            </foreignObject>
          )}
          
          {/* Room-to-room label text */}
          {isRoomToRoom && (
            <text
              x="12"
              y="5"
              fill="white"
              fontSize="10"
              fontWeight="600"
              className="font-sans"
            >
              Room
            </text>
          )}
        </g>
      )}

      {/* Flowing direction arrows - animate along path */}
      {/* Show arrows during execution (isFlowing/isActive) OR on hover */}
      {(isFlowing || isActive || isHovered) && (
        <>
          {[0, 1, 2].map((index) => {
            // Make arrows more visible during execution
            const isExecuting = isFlowing || isActive;
            const arrowSize = isExecuting ? 10 : 8;
            const arrowOpacity = isExecuting ? 1 : 0.8;
            const glowIntensity = isExecuting ? '6px' : '3px';
            
            return (
              <g key={`arrow-${index}`}>
                {/* Arrow shape as a path */}
                <path
                  d={`M 0,0 L ${arrowSize},${arrowSize/2} L 0,${arrowSize} Z`}
                  fill={typeConfig.color}
                  fillOpacity={arrowOpacity}
                  style={{
                    filter: `drop-shadow(0 0 ${glowIntensity} ${typeConfig.color})`,
                  }}
                >
                  {/* Animate along the edge path */}
                  <animateMotion
                    dur={isExecuting ? "1.5s" : "2s"}
                    repeatCount="indefinite"
                    begin={`${index * 0.67}s`}
                    calcMode="linear"
                  >
                    <mpath href={`#${pathId}`} />
                  </animateMotion>
                  {/* Fade in/out effect - less fade during execution */}
                  <animate
                    attributeName="opacity"
                    values={isExecuting ? "0.7;1;1;0.7" : "0;0.8;0.8;0"}
                    dur={isExecuting ? "1.5s" : "2s"}
                    repeatCount="indefinite"
                    begin={`${index * 0.67}s`}
                  />
                </path>
              </g>
            );
          })}
        </>
      )}

      {/* Data preview tooltip */}
      {isHovered && (
        <g transform={`translate(${midX}, ${midY - 30})`} className="connection-tooltip">
          {/* Tooltip background */}
          <rect
            x="-60"
            y="-15"
            width="120"
            height="30"
            rx="8"
            fill="rgba(0, 0, 0, 0.9)"
            stroke={typeConfig.color}
            strokeWidth="1"
            strokeOpacity="0.8"
          />
          
          {/* Tooltip text */}
          <text
            textAnchor="middle"
            dominantBaseline="middle"
            y="-5"
            fill="white"
            fontSize="10"
            fontFamily="monospace"
          >
            {typeConfig.label}
          </text>
          <text
            textAnchor="middle"
            dominantBaseline="middle"
            y="5"
            fill={typeConfig.color}
            fontSize="9"
            fontFamily="monospace"
          >
            {dataPreview}
          </text>
        </g>
      )}

      {/* Interactive hover area - invisible but clickable */}
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={20}
        className="cursor-pointer"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      />

      {/* Flowing particles using SVG animateMotion */}
      {/* Use source node's category color for particles */}
      {particles.map((particle) => (
        <circle
          key={particle.id}
          className="flow-particle"
          r="3"
          fill={sourceCategoryColor}
          fillOpacity="0.8"
          style={{
            filter: `drop-shadow(0 0 4px ${sourceCategoryColor}60)`,
          }}
        >
          <animateMotion
            dur="12s"
            repeatCount="indefinite"
            begin={particle.delay}
          >
            <mpath href={`#${pathId}`} />
          </animateMotion>
        </circle>
      ))}

    </g>
  );
});

CustomEdge.displayName = 'CustomEdge';