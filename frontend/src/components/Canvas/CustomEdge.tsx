/**
 * Custom edge component for React Flow
 * Optimized for "Premium/Schematic" look
 */

import { memo } from 'react';
import { getBezierPath } from 'reactflow';
import type { EdgeProps } from 'reactflow';
import { cn } from '@/utils/cn';
import { useExecutionStore } from '@/store/executionStore';

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
  markerEnd,
  selected,
}: EdgeProps) => {
  // Use standard Bezier path for smooth curves
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const { results, currentNodeId, nodeStatuses } = useExecutionStore();
  
  // Check execution status
  const sourceStatus = nodeStatuses[source] || results[source]?.status || 'idle';
  const targetStatus = nodeStatuses[target] || results[target]?.status || 'idle';
  
  // Determine edge state
  const isFlowing = sourceStatus === 'completed' && (targetStatus === 'running' || currentNodeId === target);
  const isActive = sourceStatus === 'running' || targetStatus === 'running';
  const isCompleted = sourceStatus === 'completed' && targetStatus === 'completed';

  return (
    <>
      {/* Base Path (Background/Glow) - Thicker, semi-transparent */}
      <path
        id={id}
        style={style}
        className={cn(
          "react-flow__edge-path stroke-slate-700/50 transition-all duration-500",
          selected && "stroke-purple-500/30 stroke-[4px]",
          isActive && "stroke-blue-500/20",
          isCompleted && "stroke-green-500/20"
        )}
        d={edgePath}
        markerEnd={markerEnd}
        strokeWidth={2} 
      />

      {/* Overlay Path (Animated/Foreground) - Thinner, sharper */}
      <path
        d={edgePath}
        className={cn(
          "fill-none stroke-[1.5px] transition-all duration-500",
          // Default state
          "stroke-slate-500",
          // Selected state
          selected && "stroke-purple-400",
          // Active/Flowing state
          (isFlowing || isActive) && "stroke-blue-400 animate-pulse",
          // Completed state
          isCompleted && "stroke-green-500"
        )}
        strokeDasharray={isFlowing ? "5 5" : "0"} // Dotted line when flowing
        style={{
          animation: isFlowing ? "dashdraw 0.5s linear infinite" : undefined,
        }}
      />
      
      {/* Flowing Particle (for active data transfer) */}
      {isFlowing && (
        <circle r="3" fill="#3b82f6">
          <animateMotion dur="1s" repeatCount="indefinite" path={edgePath} />
        </circle>
      )}
    </>
  );
});
