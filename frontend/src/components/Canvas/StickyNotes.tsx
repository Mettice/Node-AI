/**
 * Sticky Notes Component - Documentation and comments on canvas
 * 
 * Features:
 * - Draggable sticky notes
 * - Editable content with markdown support
 * - Color coding
 * - Resizable notes
 * - Auto-save on edit
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { StickyNote } from './CanvasInteractions';
import { 
  Edit3, 
  Trash2, 
  Move, 
  Maximize2, 
  StickyNote as StickyNoteIcon,
  Palette
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface StickyNotesProps {
  notes: StickyNote[];
  onUpdateNote: (noteId: string, updates: Partial<StickyNote>) => void;
  onDeleteNote: (noteId: string) => void;
}

const NOTE_COLORS = [
  { color: '#fef3c7', name: 'Soft Yellow' },    // Softer yellow (default)
  { color: '#fce7f3', name: 'Soft Pink' },      // Softer pink
  { color: '#d1fae5', name: 'Soft Green' },     // Softer green
  { color: '#dbeafe', name: 'Soft Blue' },      // Softer blue
  { color: '#e9d5ff', name: 'Soft Purple' },    // Softer purple
  { color: '#fed7aa', name: 'Soft Orange' },    // Softer orange
  { color: '#cffafe', name: 'Soft Cyan' },      // Softer cyan
  { color: '#ecfdf5', name: 'Soft Mint' },      // Softer mint
];

export function StickyNotes({ notes, onUpdateNote, onDeleteNote }: StickyNotesProps) {
  return (
    <div className="absolute inset-0 pointer-events-none z-5">
      {notes.map(note => (
        <StickyNoteCard
          key={note.id}
          note={note}
          onUpdate={onUpdateNote}
          onDelete={onDeleteNote}
        />
      ))}
    </div>
  );
}

interface StickyNoteCardProps {
  note: StickyNote;
  onUpdate: (noteId: string, updates: Partial<StickyNote>) => void;
  onDelete: (noteId: string) => void;
}

function StickyNoteCard({ note, onUpdate, onDelete }: StickyNoteCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const [editContent, setEditContent] = useState(note.content);
  const [showColorPicker, setShowColorPicker] = useState(false);
  
  const noteRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dragStartPos = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const resizeStartPos = useRef<{ x: number; y: number; width: number; height: number }>({ 
    x: 0, y: 0, width: 0, height: 0 
  });

  // Auto-focus textarea when editing starts
  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.select();
    }
  }, [isEditing]);

  const handleEditStart = useCallback(() => {
    setIsEditing(true);
    setEditContent(note.content);
  }, [note.content]);

  const handleEditSave = useCallback(() => {
    if (editContent.trim() !== note.content) {
      onUpdate(note.id, { content: editContent.trim() });
    }
    setIsEditing(false);
  }, [note.id, note.content, editContent, onUpdate]);

  const handleEditCancel = useCallback(() => {
    setEditContent(note.content);
    setIsEditing(false);
  }, [note.content]);

  // Drag functionality
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (isEditing || isResizing) return;
    
    setIsDragging(true);
    dragStartPos.current = {
      x: e.clientX - note.position.x,
      y: e.clientY - note.position.y
    };
    
    e.preventDefault();
  }, [isEditing, isResizing, note.position]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      const newPosition = {
        x: e.clientX - dragStartPos.current.x,
        y: e.clientY - dragStartPos.current.y
      };
      onUpdate(note.id, { position: newPosition });
    } else if (isResizing) {
      const newSize = {
        width: Math.max(150, e.clientX - note.position.x),
        height: Math.max(100, e.clientY - note.position.y)
      };
      onUpdate(note.id, { size: newSize });
    }
  }, [isDragging, isResizing, note.id, note.position, onUpdate]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setIsResizing(false);
  }, []);

  // Resize functionality
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    setIsResizing(true);
    resizeStartPos.current = {
      x: e.clientX,
      y: e.clientY,
      width: note.size.width,
      height: note.size.height
    };
    e.stopPropagation();
    e.preventDefault();
  }, [note.size]);

  useEffect(() => {
    if (isDragging || isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, isResizing, handleMouseMove, handleMouseUp]);

  const handleColorChange = useCallback((color: string) => {
    onUpdate(note.id, { color });
    setShowColorPicker(false);
  }, [note.id, onUpdate]);

  // Format content with simple markdown-like formatting
  const formatContent = useCallback((content: string) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>');
  }, []);

  return (
    <div
      ref={noteRef}
      className={cn(
        "absolute pointer-events-auto transition-all duration-200",
        isDragging && "cursor-grabbing shadow-2xl scale-105",
        isResizing && "cursor-se-resize"
      )}
      style={{
        left: note.position.x,
        top: note.position.y,
        width: note.size.width,
        height: note.size.height,
        zIndex: isDragging || isResizing ? 100 : 10,
      }}
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => {
        setShowControls(false);
        setShowColorPicker(false);
      }}
    >
      {/* Note paper background with slight rotation for realism */}
      <div
        className="absolute inset-0 rounded-lg shadow-lg transition-all duration-200"
        style={{
          backgroundColor: note.color,
          boxShadow: `0 4px 12px ${note.color}40, 0 0 0 1px ${note.color}60`,
          transform: isDragging ? 'rotate(2deg)' : 'rotate(1deg)',
        }}
      />

      {/* Header with drag handle */}
      <div
        className={cn(
          "relative h-8 flex items-center justify-between px-3 cursor-grab rounded-t-lg",
          isDragging && "cursor-grabbing"
        )}
        onMouseDown={handleMouseDown}
        style={{
          backgroundColor: note.color + 'CC',
        }}
      >
        <div className="flex items-center gap-2">
          <StickyNoteIcon className="w-4 h-4 text-black/40" />
          <span className="text-xs font-medium text-black/60">Note</span>
        </div>

        {/* Controls */}
        {showControls && !isEditing && (
          <div className="flex items-center gap-1">
            {/* Color picker */}
            <div className="relative">
              <button
                onClick={() => setShowColorPicker(!showColorPicker)}
                className="p-1 hover:bg-black/10 rounded transition-colors"
                title="Change color"
              >
                <Palette className="w-3 h-3 text-black/60" />
              </button>
              
              {showColorPicker && (
                <div className="absolute top-full right-0 mt-1 bg-white rounded-lg shadow-lg border p-2 flex flex-wrap gap-1 w-32 z-50">
                  {NOTE_COLORS.map(({ color, name }) => (
                    <button
                      key={color}
                      onClick={() => handleColorChange(color)}
                      className={cn(
                        "w-6 h-6 rounded border-2 transition-transform hover:scale-110",
                        note.color === color ? "border-black/40" : "border-transparent"
                      )}
                      style={{ backgroundColor: color }}
                      title={name}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Edit button */}
            <button
              onClick={handleEditStart}
              className="p-1 hover:bg-black/10 rounded transition-colors"
              title="Edit note"
            >
              <Edit3 className="w-3 h-3 text-black/60" />
            </button>

            {/* Delete button */}
            <button
              onClick={() => onDelete(note.id)}
              className="p-1 hover:bg-red-500/20 rounded transition-colors"
              title="Delete note"
            >
              <Trash2 className="w-3 h-3 text-black/60 hover:text-red-600" />
            </button>
          </div>
        )}
      </div>

      {/* Content area */}
      <div className="relative p-3 h-[calc(100%-2rem)] overflow-hidden">
        {isEditing ? (
          <textarea
            ref={textareaRef}
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            onBlur={handleEditSave}
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                handleEditCancel();
              }
              if (e.key === 'Enter' && e.metaKey) {
                handleEditSave();
              }
            }}
            className="w-full h-full bg-transparent border-none outline-none resize-none text-sm text-black/80 placeholder-black/40"
            placeholder="Type your note here... (⌘+Enter to save, Esc to cancel)"
            style={{ fontFamily: 'inherit' }}
          />
        ) : (
          <div
            className="w-full h-full text-sm text-black/80 leading-relaxed cursor-text"
            onClick={handleEditStart}
            dangerouslySetInnerHTML={{
              __html: formatContent(note.content) || '<em class="text-black/40">Click to edit...</em>'
            }}
          />
        )}
      </div>

      {/* Resize handle */}
      {showControls && !isEditing && (
        <div
          className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize opacity-40 hover:opacity-80 transition-opacity"
          onMouseDown={handleResizeStart}
          style={{
            background: `linear-gradient(-45deg, transparent 30%, ${note.color}80 31%, ${note.color}80 69%, transparent 70%)`
          }}
        />
      )}

      {/* Subtle fold effect in top-right corner */}
      <div
        className="absolute top-0 right-0 w-4 h-4 opacity-20"
        style={{
          background: `linear-gradient(-135deg, transparent 50%, ${note.color}80 51%)`,
          clipPath: 'polygon(100% 0, 0 100%, 100% 100%)'
        }}
      />
    </div>
  );
}