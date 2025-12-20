/**
 * Floating Plus Button - Opens node palette popup (draggable within canvas)
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Plus } from 'lucide-react';
import { NodePalettePopup } from './NodePalettePopup';
import { cn } from '@/utils/cn';
import { useWorkflowStore } from '@/store/workflowStore';

export function AddNodeButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [position, setPosition] = useState({ x: 400, y: 80 });
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [dragStartTime, setDragStartTime] = useState(0);
  const [hasDragged, setHasDragged] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  
  // Get nodes from store to check if canvas is empty
  const { nodes } = useWorkflowStore();

  // Initialize position from localStorage and detect mobile screen size
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    // Load saved position from localStorage
    const saved = localStorage.getItem('addNodeButtonPosition');
    if (saved) {
      try {
        const savedPosition = JSON.parse(saved);
        setPosition(savedPosition);
      } catch {
        // Use default position if parsing fails
        setPosition({ x: 400, y: 80 });
      }
    } else {
      // Set initial position to top-right area
      setPosition({ x: 400, y: 80 });
    }
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Save position to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('addNodeButtonPosition', JSON.stringify(position));
  }, [position]);

  const handleMouseDown = (e: React.MouseEvent) => {
    // Allow dragging on all devices now
    if (e.button !== 0) return; 
    e.preventDefault();
    e.stopPropagation();
    
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      // Calculate offset from mouse position to button center
      const offsetX = e.clientX - (rect.left + rect.width / 2);
      const offsetY = e.clientY - (rect.top + rect.height / 2);
      setDragOffset({ x: offsetX, y: offsetY });
      setDragStartTime(Date.now());
      setHasDragged(false);
      setIsDragging(true);
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (buttonRef.current && e.touches.length === 1) {
      const rect = buttonRef.current.getBoundingClientRect();
      const touch = e.touches[0];
      // Calculate offset from touch position to button center
      const offsetX = touch.clientX - (rect.left + rect.width / 2);
      const offsetY = touch.clientY - (rect.top + rect.height / 2);
      setDragOffset({ x: offsetX, y: offsetY });
      setDragStartTime(Date.now());
      setHasDragged(false);
      setIsDragging(true);
    }
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      updatePosition(e.clientX, e.clientY);
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 1) {
        e.preventDefault();
        const touch = e.touches[0];
        updatePosition(touch.clientX, touch.clientY);
      }
    };

    const updatePosition = (clientX: number, clientY: number) => {
      // Find the canvas container (the relative positioned parent)
      // The button is inside a wrapper div, so we need the parent of the wrapper
      const wrapperDiv = buttonRef.current?.parentElement;
      const canvasContainer = wrapperDiv?.parentElement;
      
      if (!canvasContainer || !buttonRef.current) {
        return;
      }

      const containerRect = canvasContainer.getBoundingClientRect();
      
      // Calculate new position: mouse position minus container offset minus drag offset
      // This positions the button center at the mouse position accounting for where we clicked
      const newX = clientX - containerRect.left - dragOffset.x;
      const newY = clientY - containerRect.top - dragOffset.y;

      // Constrain to canvas bounds with reasonable padding
      const buttonSize = isMobile ? 48 : 56;
      const padding = 20;
      const constrainedX = Math.max(padding, Math.min(newX, containerRect.width - buttonSize - padding));
      const constrainedY = Math.max(padding, Math.min(newY, containerRect.height - buttonSize - padding));

      setPosition({ x: constrainedX, y: constrainedY });
      setHasDragged(true);
    };

    const handleEnd = (e?: MouseEvent | TouchEvent) => {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleEnd);
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleEnd);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleEnd);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleEnd);
    };
  }, [isDragging, dragOffset, isMobile]);

  const handleClick = useCallback((e: React.MouseEvent) => {
    // Only open if we didn't just drag or if it was a very quick click
    const timeSinceStart = Date.now() - dragStartTime;
    if (!hasDragged && timeSinceStart < 200) {
      setIsOpen(!isOpen);
    } else {
      e.preventDefault();
      e.stopPropagation();
    }
  }, [hasDragged, dragStartTime, isOpen]);

  const isEmpty = nodes.length === 0;

  return (
    <>
      {/* Add Node Button - Draggable with subtle amber glow */}
      <div
        className="absolute z-50 pointer-events-none"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
      >
        {/* Subtle ambient glow - much more subtle */}
        <div
          className={cn(
            'absolute inset-0 rounded-full transition-all duration-1000',
            'bg-amber-400/10 blur-xl scale-125',
            isHovered && 'bg-amber-400/20 scale-150',
            isEmpty && 'animate-pulse-slow'
          )}
        />
        
        {/* Main button */}
        <button
          ref={buttonRef}
          onMouseDown={handleMouseDown}
          onTouchStart={handleTouchStart}
          onClick={handleClick}
          onDragStart={(e) => e.preventDefault()}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          style={{ userSelect: 'none', WebkitUserSelect: 'none' }}
          className={cn(
            'relative rounded-full pointer-events-auto',
            'bg-gradient-to-br from-amber-400 to-amber-500',
            'hover:from-amber-300 hover:to-amber-400',
            'text-black shadow-lg shadow-amber-500/25',
            'flex items-center justify-center gap-2',
            'transition-all duration-200 ease-out',
            'border border-amber-300/40',
            'select-none overflow-hidden',
            // Size and interaction - always draggable
            isMobile ? 'w-12 h-12' : 'w-14 h-14',
            'cursor-move',
            // Hover expansion - more subtle
            isHovered && !isMobile && 'px-4 min-w-[120px]',
            // Drag and active states - less dramatic
            isDragging && 'scale-105 shadow-xl shadow-amber-500/40',
            !isDragging && 'hover:scale-105 active:scale-95'
          )}
          title="Add Node (Drag to move)"
        >
          {/* Subtle inner highlight */}
          <div
            className={cn(
              'absolute inset-0 rounded-full',
              'bg-gradient-to-t from-transparent via-white/10 to-white/20',
              'transition-opacity duration-200',
              isHovered ? 'opacity-100' : 'opacity-70'
            )}
          />
          
          {/* Icon */}
          <Plus className={cn(
            'relative z-10 transition-all duration-200',
            isMobile ? "w-5 h-5" : "w-6 h-6",
            isHovered && !isMobile && 'mr-2'
          )} />
          
          {/* Hover text - only on desktop */}
          {isHovered && !isMobile && (
            <span className="relative z-10 font-medium text-sm whitespace-nowrap animate-fade-in">
              Add Node
            </span>
          )}
        </button>
      </div>

      {/* Node Palette - Bottom drawer on mobile, popup on desktop */}
      {isOpen && (
        <NodePalettePopup
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          position={position}
          isMobile={isMobile}
        />
      )}
    </>
  );
}

