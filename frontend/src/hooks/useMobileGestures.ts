/**
 * Custom hook for handling mobile gestures on React Flow canvas
 */

import { useCallback, useRef, useEffect } from 'react';
import { useReactFlow } from 'reactflow';

interface TouchPoint {
  x: number;
  y: number;
  id: number;
}

interface GestureState {
  isPinching: boolean;
  isPanning: boolean;
  lastPinchDistance: number;
  initialZoom: number;
  panStart: { x: number; y: number } | null;
  lastTouchTime: number;
  tapCount: number;
}

interface UseMobileGesturesOptions {
  onDoubleTap?: (x: number, y: number) => void;
  onLongPress?: (x: number, y: number) => void;
  enablePinchZoom?: boolean;
  enablePanning?: boolean;
  longPressDelay?: number;
}

export function useMobileGestures({
  onDoubleTap,
  onLongPress,
  enablePinchZoom = true,
  enablePanning = true,
  longPressDelay = 500,
}: UseMobileGesturesOptions = {}) {
  const { setViewport, getViewport, getZoom, setCenter } = useReactFlow();
  const gestureState = useRef<GestureState>({
    isPinching: false,
    isPanning: false,
    lastPinchDistance: 0,
    initialZoom: 1,
    panStart: null,
    lastTouchTime: 0,
    tapCount: 0,
  });
  const longPressTimer = useRef<NodeJS.Timeout>();
  const doubleTapTimer = useRef<NodeJS.Timeout>();

  // Helper function to get distance between two touch points
  const getTouchDistance = useCallback((touches: TouchList): number => {
    if (touches.length < 2) return 0;
    const touch1 = touches[0];
    const touch2 = touches[1];
    return Math.sqrt(
      Math.pow(touch2.clientX - touch1.clientX, 2) + 
      Math.pow(touch2.clientY - touch1.clientY, 2)
    );
  }, []);

  // Helper function to get center point between touches
  const getTouchCenter = useCallback((touches: TouchList): { x: number; y: number } => {
    if (touches.length === 1) {
      return { x: touches[0].clientX, y: touches[0].clientY };
    }
    const x = (touches[0].clientX + touches[1].clientX) / 2;
    const y = (touches[0].clientY + touches[1].clientY) / 2;
    return { x, y };
  }, []);

  // Handle touch start
  const handleTouchStart = useCallback((e: TouchEvent) => {
    const touches = e.touches;
    const now = Date.now();
    
    // Clear any existing timers
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
    }
    if (doubleTapTimer.current) {
      clearTimeout(doubleTapTimer.current);
    }

    if (touches.length === 1) {
      // Single touch - could be tap, long press, or pan start
      const touch = touches[0];
      const timeDelta = now - gestureState.current.lastTouchTime;
      
      // Check for double tap
      if (timeDelta < 300) {
        gestureState.current.tapCount++;
        if (gestureState.current.tapCount === 2 && onDoubleTap) {
          onDoubleTap(touch.clientX, touch.clientY);
          gestureState.current.tapCount = 0;
          return;
        }
      } else {
        gestureState.current.tapCount = 1;
      }
      
      gestureState.current.lastTouchTime = now;
      gestureState.current.panStart = { x: touch.clientX, y: touch.clientY };
      
      // Start long press timer
      if (onLongPress) {
        longPressTimer.current = setTimeout(() => {
          if (gestureState.current.panStart) {
            onLongPress(touch.clientX, touch.clientY);
          }
        }, longPressDelay);
      }
      
    } else if (touches.length === 2 && enablePinchZoom) {
      // Two touches - start pinch zoom
      gestureState.current.isPinching = true;
      gestureState.current.lastPinchDistance = getTouchDistance(touches);
      gestureState.current.initialZoom = getZoom();
      
      // Cancel single touch actions
      gestureState.current.panStart = null;
      if (longPressTimer.current) {
        clearTimeout(longPressTimer.current);
      }
    }
  }, [onDoubleTap, onLongPress, longPressDelay, enablePinchZoom, getTouchDistance, getZoom]);

  // Handle touch move
  const handleTouchMove = useCallback((e: TouchEvent) => {
    e.preventDefault(); // Prevent default scroll behavior
    
    const touches = e.touches;
    
    if (touches.length === 1 && gestureState.current.panStart && enablePanning) {
      // Single touch pan
      const touch = touches[0];
      const deltaX = touch.clientX - gestureState.current.panStart.x;
      const deltaY = touch.clientY - gestureState.current.panStart.y;
      
      // Cancel long press if we're panning
      if (longPressTimer.current && (Math.abs(deltaX) > 10 || Math.abs(deltaY) > 10)) {
        clearTimeout(longPressTimer.current);
        gestureState.current.isPanning = true;
      }
      
      // Apply pan
      if (gestureState.current.isPanning) {
        const viewport = getViewport();
        setViewport({
          x: viewport.x + deltaX,
          y: viewport.y + deltaY,
          zoom: viewport.zoom,
        });
        gestureState.current.panStart = { x: touch.clientX, y: touch.clientY };
      }
      
    } else if (touches.length === 2 && gestureState.current.isPinching && enablePinchZoom) {
      // Two touch pinch zoom
      const currentDistance = getTouchDistance(touches);
      const center = getTouchCenter(touches);
      
      if (gestureState.current.lastPinchDistance > 0) {
        const scale = currentDistance / gestureState.current.lastPinchDistance;
        const newZoom = Math.max(0.1, Math.min(2, gestureState.current.initialZoom * scale));
        
        // Apply zoom centered on gesture
        const viewport = getViewport();
        const viewportRect = (e.target as HTMLElement).getBoundingClientRect();
        const relativeCenter = {
          x: center.x - viewportRect.left,
          y: center.y - viewportRect.top,
        };
        
        setViewport({
          ...viewport,
          zoom: newZoom,
        });
      }
    }
  }, [enablePanning, enablePinchZoom, getTouchDistance, getTouchCenter, getViewport, setViewport]);

  // Handle touch end
  const handleTouchEnd = useCallback((e: TouchEvent) => {
    const touches = e.touches;
    
    // Clear timers
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
    }
    
    if (touches.length === 0) {
      // All touches ended
      gestureState.current.isPinching = false;
      gestureState.current.isPanning = false;
      gestureState.current.panStart = null;
      
      // Set double tap timer
      if (gestureState.current.tapCount === 1) {
        doubleTapTimer.current = setTimeout(() => {
          gestureState.current.tapCount = 0;
        }, 300);
      }
    } else if (touches.length === 1 && gestureState.current.isPinching) {
      // One touch remaining after pinch
      gestureState.current.isPinching = false;
      gestureState.current.panStart = { 
        x: touches[0].clientX, 
        y: touches[0].clientY 
      };
    }
  }, []);

  // Attach event listeners
  useEffect(() => {
    const canvas = document.querySelector('.react-flow__pane');
    if (!canvas) return;

    canvas.addEventListener('touchstart', handleTouchStart, { passive: false });
    canvas.addEventListener('touchmove', handleTouchMove, { passive: false });
    canvas.addEventListener('touchend', handleTouchEnd, { passive: false });

    return () => {
      canvas.removeEventListener('touchstart', handleTouchStart);
      canvas.removeEventListener('touchmove', handleTouchMove);
      canvas.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  return {
    isGesturing: gestureState.current.isPinching || gestureState.current.isPanning,
    isPinching: gestureState.current.isPinching,
    isPanning: gestureState.current.isPanning,
  };
}