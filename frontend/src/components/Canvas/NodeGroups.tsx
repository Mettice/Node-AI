/**
 * Node Groups/Frames Component - Visual grouping for related nodes
 * 
 * Features:
 * - Visual frames around grouped nodes
 * - Collapsible groups
 * - Labeled groups with editable names
 * - Color-coded groups
 * - Drag group to move all contained nodes
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { NodeGroup } from './CanvasInteractions';
import { 
  ChevronDown, 
  ChevronRight, 
  Edit3, 
  Trash2, 
  Maximize2, 
  Minimize2 
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface NodeGroupsProps {
  groups: NodeGroup[];
  onUpdateGroup: (groupId: string, updates: Partial<NodeGroup>) => void;
  onDeleteGroup: (groupId: string) => void;
  nodes: Array<{ id: string; position: { x: number; y: number } }>;
  onSelectNodes?: (nodeIds: string[]) => void;
}

const GROUP_COLORS = [
  '#3b82f6', // Blue
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#ef4444', // Red
  '#8b5cf6', // Violet
  '#ec4899', // Pink
  '#06b6d4', // Cyan
  '#84cc16', // Lime
];

export function NodeGroups({ groups, onUpdateGroup, onDeleteGroup, nodes, onSelectNodes }: NodeGroupsProps) {
  const [editingGroup, setEditingGroup] = useState<string | null>(null);
  const [editingLabel, setEditingLabel] = useState('');

  const handleEditStart = useCallback((group: NodeGroup) => {
    setEditingGroup(group.id);
    setEditingLabel(group.label);
  }, []);

  const handleEditSave = useCallback(() => {
    if (editingGroup && editingLabel.trim()) {
      onUpdateGroup(editingGroup, { label: editingLabel.trim() });
    }
    setEditingGroup(null);
    setEditingLabel('');
  }, [editingGroup, editingLabel, onUpdateGroup]);

  const handleEditCancel = useCallback(() => {
    setEditingGroup(null);
    setEditingLabel('');
  }, []);

  return (
    <>
      {/* Compact group indicators - small badges on nodes and floating label */}
      {groups.map(group => (
        <GroupIndicator
          key={group.id}
          group={group}
          isEditing={editingGroup === group.id}
          editingLabel={editingLabel}
          onEditingLabelChange={setEditingLabel}
          onEditStart={() => handleEditStart(group)}
          onEditSave={handleEditSave}
          onEditCancel={handleEditCancel}
          onUpdateGroup={onUpdateGroup}
          onDeleteGroup={onDeleteGroup}
          nodes={nodes}
          onSelectNodes={onSelectNodes}
        />
      ))}
    </>
  );
}

// Compact group indicator - shows small badge on nodes and floating label
interface GroupIndicatorProps {
  group: NodeGroup;
  isEditing: boolean;
  editingLabel: string;
  onEditingLabelChange: (label: string) => void;
  onEditStart: () => void;
  onEditSave: () => void;
  onEditCancel: () => void;
  onUpdateGroup: (groupId: string, updates: Partial<NodeGroup>) => void;
  onDeleteGroup: (groupId: string) => void;
  nodes: Array<{ id: string; position: { x: number; y: number } }>;
  onSelectNodes?: (nodeIds: string[]) => void;
}

function GroupIndicator({
  group,
  isEditing,
  editingLabel,
  onEditingLabelChange,
  onEditStart,
  onEditSave,
  onEditCancel,
  onUpdateGroup,
  onDeleteGroup,
  nodes,
  onSelectNodes,
}: GroupIndicatorProps) {
  const [showControls, setShowControls] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const labelRef = useRef<HTMLDivElement>(null);

  // Get node positions for badges
  const groupNodePositions = nodes
    .filter(n => group.nodeIds.includes(n.id))
    .map(n => ({ id: n.id, x: n.position.x, y: n.position.y }));

  // Calculate label position - always relative to first node's top-right
  // labelPosition stores offset from the first node's top-right position
  const getLabelPosition = useCallback(() => {
    const firstNode = nodes.find(n => group.nodeIds.includes(n.id));
    if (!firstNode) {
      return { x: group.position.x + group.size.width - 10, y: group.position.y - 25 };
    }
    
    const baseX = firstNode.position.x + 170; // Top-right of node (190px width - 20px offset)
    const baseY = firstNode.position.y - 5;
    
    // If we have a custom offset, apply it to the current base position
    if (group.labelOffset) {
      // Use the stored offset directly
      return {
        x: baseX + group.labelOffset.x,
        y: baseY + group.labelOffset.y
      };
    }
    
    // Fallback: if we have labelPosition but no offset, calculate it
    if (group.labelPosition) {
      // This shouldn't happen, but handle it for backwards compatibility
      const offsetX = group.labelPosition.x - baseX;
      const offsetY = group.labelPosition.y - baseY;
      return {
        x: baseX + offsetX,
        y: baseY + offsetY
      };
    }
    
    // Default: position on top-right of first node
    return {
      x: baseX,
      y: baseY
    };
  }, [group, nodes]);

  const labelPosition = getLabelPosition();

  const handleSelectGroup = useCallback(() => {
    if (onSelectNodes && !isEditing && !isDragging) {
      onSelectNodes(group.nodeIds);
    }
  }, [onSelectNodes, group.nodeIds, isEditing, isDragging]);

  // Handle label drag - allow dragging even when editing (but not on the input itself)
  const handleLabelMouseDown = useCallback((e: React.MouseEvent) => {
    // Don't drag if clicking on the input field
    const target = e.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.closest('input')) {
      return;
    }
    e.preventDefault();
    e.stopPropagation();
    
    if (labelRef.current) {
      // Find the canvas container - the parent div with class "flex-1 relative"
      const container = labelRef.current.closest('.flex-1.relative');
      if (!container) {
        // Fallback: find any parent with relative positioning
        const fallback = labelRef.current.parentElement?.closest('[class*="relative"]');
        if (!fallback) return;
        const containerRect = fallback.getBoundingClientRect();
        setDragOffset({
          x: e.clientX - containerRect.left - labelPosition.x,
          y: e.clientY - containerRect.top - labelPosition.y,
        });
        setIsDragging(true);
        return;
      }
      
      const containerRect = container.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - containerRect.left - labelPosition.x,
        y: e.clientY - containerRect.top - labelPosition.y,
      });
      setIsDragging(true);
    }
  }, [isEditing, labelPosition]);

  // Handle label drag move
  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      // Find the canvas container
      const container = labelRef.current?.closest('.flex-1.relative');
      if (!container) {
        // Fallback
        const fallback = labelRef.current?.parentElement?.closest('[class*="relative"]');
        if (!fallback) return;
        const containerRect = fallback.getBoundingClientRect();
        const newX = e.clientX - containerRect.left - dragOffset.x;
        const newY = e.clientY - containerRect.top - dragOffset.y;
        const labelWidth = 150;
        const labelHeight = 35;
        const padding = 10;
        const constrainedX = Math.max(padding, Math.min(newX, containerRect.width - labelWidth - padding));
        const constrainedY = Math.max(padding, Math.min(newY, containerRect.height - labelHeight - padding));
        // Store absolute position and calculate offset from first node's top-right
        const firstNode = nodes.find(n => group.nodeIds.includes(n.id));
        if (firstNode) {
          const baseX = firstNode.position.x + 260;
          const baseY = firstNode.position.y - 5;
          const offsetX = constrainedX - baseX;
          const offsetY = constrainedY - baseY;
          
          onUpdateGroup(group.id, {
            labelPosition: { x: constrainedX, y: constrainedY },
            labelOffset: { x: offsetX, y: offsetY }
          });
        }
        return;
      }

      const containerRect = container.getBoundingClientRect();
      const newX = e.clientX - containerRect.left - dragOffset.x;
      const newY = e.clientY - containerRect.top - dragOffset.y;

      // Constrain to canvas bounds
      const labelWidth = 150; // Approximate label width
      const labelHeight = 35;
      const padding = 10;
      const constrainedX = Math.max(padding, Math.min(newX, containerRect.width - labelWidth - padding));
      const constrainedY = Math.max(padding, Math.min(newY, containerRect.height - labelHeight - padding));

      // Store absolute position and calculate offset from first node's top-right
      const firstNode = nodes.find(n => group.nodeIds.includes(n.id));
      if (firstNode) {
        const baseX = firstNode.position.x + 260;
        const baseY = firstNode.position.y - 5;
        const offsetX = constrainedX - baseX;
        const offsetY = constrainedY - baseY;
        
        onUpdateGroup(group.id, {
          labelPosition: { x: constrainedX, y: constrainedY },
          labelOffset: { x: offsetX, y: offsetY }
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset, group.id, onUpdateGroup]);

  return (
    <>
      {/* Floating compact label - draggable and positioned on nodes */}
      <div
        ref={labelRef}
        className="absolute pointer-events-auto z-10"
        style={{
          left: `${labelPosition.x}px`,
          top: `${labelPosition.y}px`,
          transform: 'translateX(-100%)', // Align to right edge
          cursor: isDragging ? 'grabbing' : 'grab',
        }}
        onMouseDown={handleLabelMouseDown}
        onMouseEnter={() => setShowControls(true)}
        onMouseLeave={() => setShowControls(false)}
      >
        <div
          className="glass border rounded-lg px-2 py-1 flex items-center gap-2 shadow-lg"
          style={{
            borderColor: group.color + '60',
            backgroundColor: group.color + '15',
          }}
        >
          {isEditing ? (
            <input
              type="text"
              value={editingLabel}
              onChange={(e) => onEditingLabelChange(e.target.value)}
              onBlur={onEditSave}
              onKeyDown={(e) => {
                if (e.key === 'Enter') onEditSave();
                if (e.key === 'Escape') onEditCancel();
              }}
              className="bg-transparent border-none outline-none text-xs font-medium text-white min-w-[80px]"
              style={{ color: group.color }}
              autoFocus
            />
          ) : (
            <span
              className="text-xs font-medium cursor-pointer hover:underline"
              style={{ color: group.color }}
              onClick={(e) => {
                e.stopPropagation();
                // Double-click to edit, single click to select
                if (e.detail === 2) {
                  onEditStart();
                } else {
                  handleSelectGroup();
                }
              }}
              title={`${group.label} - Click to select all nodes, double-click to edit name`}
            >
              {group.label}
            </span>
          )}

          {showControls && !isEditing && (
            <div className="flex items-center gap-1 ml-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (onSelectNodes) {
                    onSelectNodes(group.nodeIds);
                  }
                }}
                className="p-0.5 hover:bg-white/10 rounded transition-colors"
                title="Select all nodes in group"
              >
                <Maximize2 className="w-3 h-3 text-slate-400 hover:text-white" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteGroup(group.id);
                }}
                className="p-0.5 hover:bg-red-500/20 rounded transition-colors"
                title="Delete group"
              >
                <Trash2 className="w-3 h-3 text-slate-400 hover:text-red-400" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Small colored badges on each node in the group */}
      {groupNodePositions.map(({ id, x, y }) => (
        <div
          key={id}
          className="absolute pointer-events-none z-20"
          style={{
            left: `${x + 170}px`, // Right side of node (190px width - 20px offset)
            top: `${y + 5}px`, // Top of node
          }}
        >
          <div
            className="w-3 h-3 rounded-full border-2 border-slate-900 shadow-lg"
            style={{
              backgroundColor: group.color,
            }}
            title={group.label}
          />
        </div>
      ))}
    </>
  );
}

interface GroupFrameProps {
  group: NodeGroup;
  isEditing: boolean;
  editingLabel: string;
  onEditingLabelChange: (label: string) => void;
  onEditStart: () => void;
  onEditSave: () => void;
  onEditCancel: () => void;
  onUpdateGroup: (groupId: string, updates: Partial<NodeGroup>) => void;
  onDeleteGroup: (groupId: string) => void;
}

function GroupFrame({
  group,
  isEditing,
  editingLabel,
  onEditingLabelChange,
  onEditStart,
  onEditSave,
  onEditCancel,
  onUpdateGroup,
  onDeleteGroup,
}: GroupFrameProps) {
  const [showControls, setShowControls] = useState(false);

  const handleColorChange = useCallback((color: string) => {
    onUpdateGroup(group.id, { color });
  }, [group.id, onUpdateGroup]);

  const handleToggleCollapsed = useCallback(() => {
    onUpdateGroup(group.id, { collapsed: !group.collapsed });
  }, [group.id, group.collapsed, onUpdateGroup]);

  return (
    <div
      className="absolute pointer-events-auto"
      style={{
        left: group.position.x,
        top: group.position.y,
        width: group.size.width,
        height: group.collapsed ? 40 : group.size.height,
      }}
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => setShowControls(false)}
    >
      {/* Group frame background */}
      <div
        className={cn(
          "absolute inset-0 rounded-lg border-2 transition-all duration-300",
          group.collapsed ? "bg-black/20" : "bg-black/5"
        )}
        style={{
          borderColor: group.color + '60',
          backgroundColor: group.color + '0A',
        }}
      />

      {/* Group header */}
      <div
        className="absolute top-0 left-0 right-0 h-10 flex items-center justify-between px-3 rounded-t-lg"
        style={{
          background: `linear-gradient(135deg, ${group.color}20, ${group.color}10)`,
          borderBottom: group.collapsed ? 'none' : `1px solid ${group.color}30`,
        }}
      >
        <div className="flex items-center gap-2">
          {/* Collapse/Expand button */}
          <button
            onClick={handleToggleCollapsed}
            className="p-1 hover:bg-white/10 rounded transition-colors"
            title={group.collapsed ? 'Expand group' : 'Collapse group'}
          >
            {group.collapsed ? (
              <ChevronRight className="w-3 h-3 text-slate-300" />
            ) : (
              <ChevronDown className="w-3 h-3 text-slate-300" />
            )}
          </button>

          {/* Group label */}
          {isEditing ? (
            <input
              type="text"
              value={editingLabel}
              onChange={(e) => onEditingLabelChange(e.target.value)}
              onBlur={onEditSave}
              onKeyDown={(e) => {
                if (e.key === 'Enter') onEditSave();
                if (e.key === 'Escape') onEditCancel();
              }}
              className="bg-transparent border-none outline-none text-sm font-medium text-white"
              style={{ color: group.color }}
              autoFocus
            />
          ) : (
            <span
              className="text-sm font-medium cursor-pointer"
              style={{ color: group.color }}
              onClick={onEditStart}
            >
              {group.label}
            </span>
          )}

          <span className="text-xs text-slate-500">
            ({group.nodeIds.length} nodes)
          </span>
        </div>

        {/* Controls */}
        {showControls && !isEditing && (
          <div className="flex items-center gap-1">
            {/* Color picker */}
            <div className="flex gap-1">
              {GROUP_COLORS.slice(0, 4).map(color => (
                <button
                  key={color}
                  onClick={() => handleColorChange(color)}
                  className={cn(
                    "w-3 h-3 rounded-full border-2 transition-transform hover:scale-110",
                    group.color === color ? "border-white" : "border-transparent"
                  )}
                  style={{ backgroundColor: color }}
                  title="Change color"
                />
              ))}
            </div>

            {/* Edit button */}
            <button
              onClick={onEditStart}
              className="p-1 hover:bg-white/10 rounded transition-colors"
              title="Edit label"
            >
              <Edit3 className="w-3 h-3 text-slate-400" />
            </button>

            {/* Delete button */}
            <button
              onClick={() => onDeleteGroup(group.id)}
              className="p-1 hover:bg-red-500/20 rounded transition-colors"
              title="Delete group"
            >
              <Trash2 className="w-3 h-3 text-slate-400 hover:text-red-400" />
            </button>
          </div>
        )}
      </div>

      {/* Group content area (when expanded) */}
      {!group.collapsed && (
        <div className="absolute top-10 inset-x-0 bottom-0 rounded-b-lg overflow-hidden">
          {/* Pattern overlay for visual depth */}
          <div
            className="absolute inset-0 opacity-5"
            style={{
              background: `repeating-linear-gradient(
                45deg,
                ${group.color}00 0px,
                ${group.color}00 10px,
                ${group.color}20 10px,
                ${group.color}20 11px
              )`
            }}
          />
        </div>
      )}

      {/* Resize handle (bottom-right corner) */}
      {!group.collapsed && showControls && (
        <div
          className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize"
          style={{
            background: `linear-gradient(-45deg, transparent 30%, ${group.color}60 31%, ${group.color}60 69%, transparent 70%)`
          }}
        />
      )}
    </div>
  );
}