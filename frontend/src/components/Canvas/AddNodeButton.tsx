/**
 * Floating Plus Button - Opens node palette popup (draggable within canvas)
 */

import { useState, useRef, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { NodePalettePopup } from './NodePalettePopup';
import { cn } from '@/utils/cn';

export function AddNodeButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState(() => {
    // Load saved position from localStorage or use default
    const saved = localStorage.getItem('addNodeButtonPosition');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return { x: 100, y: 100 };
      }
    }
    return { x: 100, y: 100 };
  });
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Save position to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('addNodeButtonPosition', JSON.stringify(position));
  }, [position]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Only left mouse button
    e.preventDefault();
    e.stopPropagation();
    
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - rect.left - rect.width / 2,
        y: e.clientY - rect.top - rect.height / 2,
      });
      setIsDragging(true);
    }
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      // Find the canvas container (the relative positioned parent)
      const canvasContainer = buttonRef.current?.parentElement;
      if (!canvasContainer) return;

      const containerRect = canvasContainer.getBoundingClientRect();
      const newX = e.clientX - containerRect.left - dragOffset.x - 28; // Center the button
      const newY = e.clientY - containerRect.top - dragOffset.y - 28;

      // Constrain to canvas bounds
      const buttonSize = 56; // w-14 = 56px
      const constrainedX = Math.max(0, Math.min(newX, containerRect.width - buttonSize));
      const constrainedY = Math.max(0, Math.min(newY, containerRect.height - buttonSize));

      setPosition({ x: constrainedX, y: constrainedY });
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
  }, [isDragging, dragOffset]);

  const handleClick = () => {
    // Only open if we didn't just drag
    if (!isDragging) {
      setIsOpen(!isOpen);
    }
  };

  return (
    <>
      {/* Draggable Plus Button - positioned within canvas */}
      <button
        ref={buttonRef}
        onMouseDown={handleMouseDown}
        onClick={handleClick}
        className={cn(
          'absolute z-50 w-14 h-14 rounded-full',
          'bg-purple-500 hover:bg-purple-600',
          'text-white shadow-lg shadow-purple-500/50',
          'flex items-center justify-center',
          'transition-all duration-200',
          'hover:scale-110 active:scale-95',
          'border-2 border-purple-400/30',
          'cursor-move select-none',
          isDragging && 'scale-105'
        )}
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
        title="Add Node (Drag to move)"
      >
        <Plus className="w-6 h-6" />
      </button>

      {/* Node Palette Popup */}
      {isOpen && (
        <NodePalettePopup
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          position={position}
        />
      )}
    </>
  );
}

