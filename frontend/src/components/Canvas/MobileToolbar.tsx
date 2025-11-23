/**
 * Mobile-specific toolbar for canvas actions
 */

import { useState, useEffect } from 'react';
import { 
  Home, 
  Play, 
  Square, 
  Plus, 
  Eye, 
  Settings,
  Undo2,
  Redo2,
  Save
} from 'lucide-react';
import { useWorkflowStore } from '@/store/workflowStore';
import { useExecutionStore } from '@/store/executionStore';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/utils/cn';

interface MobileToolbarProps {
  onAddNode: () => void;
  onSave: () => void;
  onRun: () => void;
  onUndo: () => void;
  onRedo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  isSaving?: boolean;
  isRunning?: boolean;
}

export function MobileToolbar({
  onAddNode,
  onSave,
  onRun,
  onUndo,
  onRedo,
  canUndo,
  canRedo,
  isSaving = false,
  isRunning = false,
}: MobileToolbarProps) {
  const { nodes } = useWorkflowStore();
  const { setActiveUtility } = useUIStore();
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  // Auto-hide toolbar on scroll (optional)
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      const isScrollingDown = currentScrollY > lastScrollY;
      
      // Only hide if scrolling down significantly
      if (isScrollingDown && currentScrollY > 50) {
        setIsVisible(false);
      } else if (!isScrollingDown) {
        setIsVisible(true);
      }
      
      setLastScrollY(currentScrollY);
    };

    // Throttled scroll handler
    let timeoutId: NodeJS.Timeout;
    const throttledHandleScroll = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(handleScroll, 100);
    };

    window.addEventListener('scroll', throttledHandleScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', throttledHandleScroll);
      clearTimeout(timeoutId);
    };
  }, [lastScrollY]);

  const toolbarButtons = [
    {
      id: 'home',
      icon: Home,
      label: 'Home',
      onClick: () => setActiveUtility('dashboard'),
      disabled: false,
    },
    {
      id: 'undo',
      icon: Undo2,
      label: 'Undo',
      onClick: onUndo,
      disabled: !canUndo,
    },
    {
      id: 'add',
      icon: Plus,
      label: 'Add',
      onClick: onAddNode,
      disabled: false,
      primary: true,
    },
    {
      id: 'redo',
      icon: Redo2,
      label: 'Redo',
      onClick: onRedo,
      disabled: !canRedo,
    },
    {
      id: 'run',
      icon: isRunning ? Square : Play,
      label: isRunning ? 'Stop' : 'Run',
      onClick: onRun,
      disabled: nodes.length === 0,
      variant: isRunning ? 'danger' : 'success',
    },
  ];

  if (!isVisible) return null;

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-50">
      {/* Backdrop blur */}
      <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm" />
      
      {/* Toolbar content */}
      <div className="relative px-4 py-3 border-t border-white/10">
        <div className="flex items-center justify-around max-w-sm mx-auto">
          {toolbarButtons.map(({ id, icon: Icon, label, onClick, disabled, primary, variant }) => (
            <button
              key={id}
              onClick={onClick}
              disabled={disabled}
              className={cn(
                'flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-all duration-200',
                'min-w-[60px] h-14',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                primary 
                  ? 'bg-purple-500 hover:bg-purple-600 text-white shadow-lg' 
                  : variant === 'danger'
                  ? 'bg-red-500 hover:bg-red-600 text-white'
                  : variant === 'success'
                  ? 'bg-green-500 hover:bg-green-600 text-white'
                  : 'text-slate-300 hover:text-white hover:bg-white/10',
                !disabled && 'hover:scale-105 active:scale-95'
              )}
              title={label}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="text-xs font-medium truncate">
                {label}
              </span>
            </button>
          ))}
        </div>
        
        {/* Quick save indicator */}
        {isSaving && (
          <div className="absolute top-1 right-4 flex items-center gap-2 text-xs text-slate-400">
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
            Saving...
          </div>
        )}
      </div>
    </div>
  );
}