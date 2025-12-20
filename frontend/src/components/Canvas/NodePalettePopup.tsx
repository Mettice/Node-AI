/**
 * Node Palette Popup - Shows when Plus button is clicked
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, Search, ChevronRight } from 'lucide-react';
import { listNodes } from '@/services/nodes';
import { NodeCard } from '@/components/Sidebar/NodeCard';
import { NODE_CATEGORY_COLORS } from '@/constants';
import type { NodeMetadata } from '@/types/node';
import { Spinner } from '@/components/common/Spinner';
import { useWorkflowStore } from '@/store/workflowStore';
import { cn } from '@/utils/cn';

// Wrapper that allows both drag and click without interfering
interface ClickableNodeCardProps {
  node: NodeMetadata;
  nodeKey: string;
  onDragStart: () => void;
  onClick: () => void;
  onMouseDown: () => void;
}

function ClickableNodeCard({ node, onDragStart, onClick, onMouseDown }: ClickableNodeCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const wasDraggedRef = useRef(false);

  useEffect(() => {
    const card = cardRef.current?.querySelector('[draggable="true"]');
    if (!card) return;

    const handleDragStart = () => {
      wasDraggedRef.current = true;
      onDragStart();
    };

    const handleClick = () => {
      if (!wasDraggedRef.current) {
        onClick();
      }
      // Reset after a delay
      setTimeout(() => {
        wasDraggedRef.current = false;
      }, 100);
    };

    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('click', handleClick);

    return () => {
      card.removeEventListener('dragstart', handleDragStart);
      card.removeEventListener('click', handleClick);
    };
  }, [onDragStart, onClick]);

  return (
    <div ref={cardRef} onMouseDown={onMouseDown}>
      <NodeCard node={node} />
    </div>
  );
}


interface NodePalettePopupProps {
  isOpen: boolean;
  onClose: () => void;
  position: { x: number; y: number };
  isMobile?: boolean;
}

const categoryLabels: Record<string, string> = {
  input: 'Input',
  processing: 'Processing',
  embedding: 'Embedding',
  storage: 'Storage',
  retrieval: 'Retrieval',
  llm: 'LLM',
  tool: 'Tool',
  memory: 'Memory',
  agent: 'Agent',
  communication: 'Communication',
  integration: 'Integration',
  // New AI categories
  intelligence: 'Intelligence',
  business: 'Business',
  content: 'Content',
  developer: 'Developer',
  sales: 'Sales',
};

export function NodePalettePopup({ isOpen, onClose, position, isMobile = false }: NodePalettePopupProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const isDraggingRef = useRef(false); // Immediate ref check (not async like state)
  const { addNode } = useWorkflowStore();
  const dragStartedRef = useRef<Record<string, boolean>>({});
  const mouseDownTimeRef = useRef<Record<string, number>>({});
  // Categories collapsed by default for cleaner UI - expand on click
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    input: false,
    processing: false,
    embedding: false,
    storage: false,
    retrieval: false,
    llm: false,
    tool: false,
    memory: false,
    agent: false,
    communication: false,
    integration: false,
    intelligence: false,
    business: false,
    content: false,
    developer: false,
    sales: false,
  });

  // Handle node click - insert at canvas center
  const handleNodeClick = useCallback((node: NodeMetadata, nodeKey: string) => {
    // Only add if drag didn't start
    if (!dragStartedRef.current[nodeKey]) {
      const newNode = {
        id: `${node.type}-${Date.now()}`,
        type: node.type,
        position: { x: 400, y: 300 }, // Center of canvas
        data: {
          label: node.name,
          category: node.category,
          status: 'idle' as const,
          config: {},
        },
      };
      addNode(newNode);
      onClose(); // Close popup after adding node
    }
    // Reset after a short delay
    setTimeout(() => {
      delete dragStartedRef.current[nodeKey];
    }, 100);
  }, [addNode, onClose]);

  // Fetch nodes from API
  const { data: nodes = [], isLoading, error } = useQuery({
    queryKey: ['nodes'],
    queryFn: listNodes,
    retry: 1,
  });

  // Group nodes by category
  const nodesByCategory = nodes?.reduce((acc, node) => {
    const category = node.category || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(node);
    return acc;
  }, {} as Record<string, NodeMetadata[]>) || {};

  // Filter nodes based on search
  const filteredNodesByCategory = Object.entries(nodesByCategory).reduce(
    (acc, [category, categoryNodes]) => {
      const filtered = categoryNodes.filter(
        (node) =>
          node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          node.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
      if (filtered.length > 0) {
        acc[category] = filtered;
      }
      return acc;
    },
    {} as Record<string, NodeMetadata[]>
  );

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [category]: !prev[category],
    }));
  };

  // Close on escape key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  // Listen for drag end globally to close popup after successful drop
  useEffect(() => {
    if (!isDragging) return;

    const handleDragEnd = () => {
      isDraggingRef.current = false;
      setIsDragging(false);
      // Close popup after drag ends (whether successful or not)
      setTimeout(() => {
        onClose();
      }, 200);
    };

    // Also listen for drop on canvas to close popup
    const handleDrop = () => {
      isDraggingRef.current = false;
      setIsDragging(false);
      setTimeout(() => {
        onClose();
      }, 100);
    };

    document.addEventListener('dragend', handleDragEnd);
    document.addEventListener('drop', handleDrop);
    
    return () => {
      document.removeEventListener('dragend', handleDragEnd);
      document.removeEventListener('drop', handleDrop);
    };
  }, [isDragging, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop - allow drag through */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={(e) => {
          // Don't close if dragging or if click came from popup
          if (!isDraggingRef.current && !isDragging && !(e.target as HTMLElement).closest('[role="dialog"]')) {
            onClose();
          }
        }}
        onKeyDown={handleKeyDown}
        // Allow drag events to pass through
        onDragOver={(e) => {
          e.preventDefault();
        }}
        style={{
          // During drag, make backdrop non-blocking
          pointerEvents: (isDragging || isDraggingRef.current) ? 'none' : 'auto',
        }}
      />

      {/* Popup - Bottom drawer on mobile, positioned popup on desktop */}
      <div
        role="dialog"
        className={cn(
          'fixed z-50 bg-slate-800/95 backdrop-blur-lg border border-white/10 shadow-2xl',
          // Mobile: bottom drawer
          isMobile 
            ? 'bottom-0 left-0 right-0 max-h-[70vh] rounded-t-lg'
            : 'w-80 max-h-[600px] rounded-lg',
          'flex flex-col',
          'glass-strong'
        )}
        style={isMobile ? {} : {
          left: `${position.x + 60}px`,
          top: `${position.y}px`,
        }}
        onKeyDown={handleKeyDown}
        onClick={(e) => {
          // Prevent clicks inside popup from closing it
          e.stopPropagation();
        }}
        // Allow drag events to pass through to canvas
        onDragOver={(e) => {
          e.preventDefault();
        }}
      >
        {/* Header */}
        <div className={cn("border-b border-white/10 flex items-center justify-between", isMobile ? "p-3" : "p-4")}>
          {isMobile && (
            <div className="w-8 h-1 bg-slate-600 rounded-full mx-auto mb-2" />
          )}
          <h2 className={cn("font-semibold text-white", isMobile ? "text-base" : "text-lg")}>
            Add Node
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors p-1 hover:bg-white/5 rounded"
            title="Close"
          >
            <X className={cn(isMobile ? "w-4 h-4" : "w-5 h-5")} />
          </button>
        </div>

        {/* Search */}
        <div className={cn("border-b border-white/10", isMobile ? "p-3" : "p-4")}>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all text-sm"
              autoFocus
            />
          </div>
        </div>

        {/* Node Categories */}
        <div className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-400">
              <p className="text-sm">Failed to load nodes</p>
            </div>
          ) : Object.keys(filteredNodesByCategory).length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <p className="text-sm">No nodes found</p>
              {searchQuery && (
                <p className="text-xs mt-2">Try a different search term</p>
              )}
            </div>
          ) : (
            Object.entries(filteredNodesByCategory).map(([category, categoryNodes]) => {
              const categoryColor = NODE_CATEGORY_COLORS[category as keyof typeof NODE_CATEGORY_COLORS] || '#9ca3af';
              const categoryLabel = categoryLabels[category] || category;
              const isExpanded = expandedCategories[category];

              return (
                <div key={category} className="mb-1">
                  {/* Category header with colored left border */}
                  <button
                    onClick={() => toggleCategory(category)}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-2.5 rounded-lg",
                      "hover:bg-white/5 transition-all duration-200",
                      "border-l-4",
                      isExpanded && "bg-white/[0.03]"
                    )}
                    style={{ 
                      borderLeftColor: categoryColor,
                    }}
                  >
                    <div className="flex items-center gap-2.5">
                      {/* Colored icon indicator */}
                      <div 
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: categoryColor }}
                      />
                      <span
                        className="text-sm font-semibold tracking-wide"
                        style={{ color: categoryColor }}
                      >
                        {categoryLabel}
                      </span>
                      <span className="text-xs text-slate-500 bg-white/5 px-1.5 py-0.5 rounded">
                        {categoryNodes.length}
                      </span>
                    </div>
                    <div 
                      className="transition-transform duration-200"
                      style={{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}
                    >
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    </div>
                  </button>

                  {/* Category nodes with animation */}
                  <div 
                    className={cn(
                      "overflow-hidden transition-all duration-200 ease-out",
                      isExpanded ? "max-h-[1000px] opacity-100" : "max-h-0 opacity-0"
                    )}
                  >
                    <div className="ml-4 mt-1 space-y-1 pb-1">
                      {categoryNodes.map((node, index) => {
                        const nodeKey = `${node.type}-${index}`;
                        
                        return (
                          <ClickableNodeCard
                            key={nodeKey}
                            node={node}
                            nodeKey={nodeKey}
                            onDragStart={() => {
                              dragStartedRef.current[nodeKey] = true;
                              isDraggingRef.current = true;
                              setIsDragging(true);
                            }}
                            onClick={() => {
                              const clickDuration = Date.now() - (mouseDownTimeRef.current[nodeKey] || 0);
                              if (!dragStartedRef.current[nodeKey] && clickDuration < 500) {
                                handleNodeClick(node, nodeKey);
                              }
                            }}
                            onMouseDown={() => {
                              mouseDownTimeRef.current[nodeKey] = Date.now();
                              dragStartedRef.current[nodeKey] = false;
                            }}
                          />
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </>
  );
}

