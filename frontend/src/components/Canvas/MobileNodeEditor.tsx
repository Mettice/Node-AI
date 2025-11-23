/**
 * Mobile-optimized node editor with touch-friendly interface
 */

import { useState, useEffect } from 'react';
import { X, Save, Trash2, Copy, Settings, ChevronRight } from 'lucide-react';
import { Node } from 'reactflow';
import { useWorkflowStore } from '@/store/workflowStore';
import { cn } from '@/utils/cn';
import { Button } from '@/components/common/Button';

interface MobileNodeEditorProps {
  node: Node;
  isOpen: boolean;
  onClose: () => void;
  onSave: (nodeData: any) => void;
  onDelete: () => void;
}

export function MobileNodeEditor({ node, isOpen, onClose, onSave, onDelete }: MobileNodeEditorProps) {
  const [nodeData, setNodeData] = useState(node.data || {});
  const [activeSection, setActiveSection] = useState<string>('basic');
  const [hasChanges, setHasChanges] = useState(false);
  
  const { duplicateNode } = useWorkflowStore();

  // Track changes
  useEffect(() => {
    const hasDataChanged = JSON.stringify(nodeData) !== JSON.stringify(node.data || {});
    setHasChanges(hasDataChanged);
  }, [nodeData, node.data]);

  // Update local state when node changes
  useEffect(() => {
    setNodeData(node.data || {});
  }, [node.data]);

  const handleSave = () => {
    onSave(nodeData);
    setHasChanges(false);
  };

  const handleDuplicate = () => {
    duplicateNode(node.id);
    onClose();
  };

  const handleFieldChange = (field: string, value: any) => {
    setNodeData(prev => ({
      ...prev,
      config: {
        ...prev.config,
        [field]: value
      }
    }));
  };

  const sections = [
    { id: 'basic', label: 'Basic', icon: Settings },
    { id: 'advanced', label: 'Advanced', icon: ChevronRight },
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      
      {/* Bottom Sheet */}
      <div className="absolute bottom-0 left-0 right-0 bg-slate-900 border-t border-white/10 rounded-t-2xl max-h-[85vh] flex flex-col">
        {/* Handle */}
        <div className="w-12 h-1 bg-slate-600 rounded-full mx-auto mt-3 mb-4" />
        
        {/* Header */}
        <div className="flex items-center justify-between px-4 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <Settings className="w-4 h-4 text-purple-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">
                {nodeData.label || node.type}
              </h2>
              <p className="text-xs text-slate-400">Node Configuration</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Section Tabs */}
        <div className="flex border-b border-white/10">
          {sections.map(section => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
                'border-b-2',
                activeSection === section.id
                  ? 'text-purple-400 border-purple-500 bg-purple-500/10'
                  : 'text-slate-400 border-transparent hover:text-slate-300'
              )}
            >
              <section.icon className="w-4 h-4" />
              {section.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {activeSection === 'basic' && (
            <>
              {/* Node Label */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Node Name
                </label>
                <input
                  type="text"
                  value={nodeData.label || ''}
                  onChange={(e) => handleFieldChange('label', e.target.value)}
                  className="w-full px-3 py-3 bg-slate-800 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 text-base"
                  placeholder="Enter node name..."
                />
              </div>

              {/* Node Description */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Description
                </label>
                <textarea
                  value={nodeData.config?.description || ''}
                  onChange={(e) => handleFieldChange('description', e.target.value)}
                  className="w-full px-3 py-3 bg-slate-800 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 text-base resize-none"
                  placeholder="Describe what this node does..."
                  rows={3}
                />
              </div>

              {/* Dynamic Fields Based on Node Type */}
              {node.type === 'text_input' && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Default Text
                  </label>
                  <textarea
                    value={nodeData.config?.text || ''}
                    onChange={(e) => handleFieldChange('text', e.target.value)}
                    className="w-full px-3 py-3 bg-slate-800 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 text-base resize-none"
                    placeholder="Enter default text..."
                    rows={4}
                  />
                </div>
              )}

              {node.type === 'chat' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Model
                    </label>
                    <select
                      value={nodeData.config?.model || 'gpt-3.5-turbo'}
                      onChange={(e) => handleFieldChange('model', e.target.value)}
                      className="w-full px-3 py-3 bg-slate-800 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 text-base"
                    >
                      <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                      <option value="gpt-4">GPT-4</option>
                      <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                      <option value="claude-3-opus">Claude 3 Opus</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      System Prompt
                    </label>
                    <textarea
                      value={nodeData.config?.system_prompt || ''}
                      onChange={(e) => handleFieldChange('system_prompt', e.target.value)}
                      className="w-full px-3 py-3 bg-slate-800 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 text-base resize-none"
                      placeholder="Enter system prompt..."
                      rows={4}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Temperature: {nodeData.config?.temperature || 0.7}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="0.1"
                      value={nodeData.config?.temperature || 0.7}
                      onChange={(e) => handleFieldChange('temperature', parseFloat(e.target.value))}
                      className="w-full h-6 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                      <span>Conservative</span>
                      <span>Creative</span>
                    </div>
                  </div>
                </>
              )}
            </>
          )}

          {activeSection === 'advanced' && (
            <>
              <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                <h3 className="text-sm font-medium text-white mb-2">Node ID</h3>
                <p className="text-xs text-slate-400 font-mono">{node.id}</p>
              </div>

              <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                <h3 className="text-sm font-medium text-white mb-2">Position</h3>
                <p className="text-xs text-slate-400 font-mono">
                  X: {Math.round(node.position.x)}, Y: {Math.round(node.position.y)}
                </p>
              </div>
            </>
          )}
        </div>

        {/* Actions */}
        <div className="p-4 border-t border-white/10 space-y-3">
          {/* Primary Actions */}
          <div className="flex gap-3">
            <Button
              onClick={handleSave}
              disabled={!hasChanges}
              className="flex-1 bg-purple-500 hover:bg-purple-600 text-white py-3"
            >
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
          </div>

          {/* Secondary Actions */}
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={handleDuplicate}
              variant="secondary"
              className="py-3"
            >
              <Copy className="w-4 h-4 mr-2" />
              Duplicate
            </Button>
            <Button
              onClick={() => {
                if (confirm('Are you sure you want to delete this node?')) {
                  onDelete();
                }
              }}
              variant="danger"
              className="py-3"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}