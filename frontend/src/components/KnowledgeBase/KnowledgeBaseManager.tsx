/**
 * Knowledge Base Manager Component
 * 
 * Manages knowledge bases: create, view, edit, process files
 */

import { useState, useEffect } from 'react';
import { Plus, Database, FileText, Clock, Tag, Settings, Play, Trash2, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';
import {
  listKnowledgeBases,
  createKnowledgeBase,
  deleteKnowledgeBase,
  getKnowledgeBase,
  type KnowledgeBaseListItem,
  type CreateKnowledgeBaseRequest,
  type ProcessingStatus,
} from '@/services/knowledgeBase';
import { KnowledgeBaseDetail } from './KnowledgeBaseDetail';
import { ProcessKnowledgeBaseModal } from './ProcessKnowledgeBaseModal';
import toast from 'react-hot-toast';

// KB Card Component
function KnowledgeBaseCard({
  kb,
  status,
  onManage,
  onProcess,
  onDelete,
}: {
  kb: KnowledgeBaseListItem;
  status?: ProcessingStatus | null;
  onManage: () => void;
  onProcess: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-3 hover:bg-white/10 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-semibold text-white truncate">{kb.name}</h4>
            {kb.is_shared && (
              <span className="px-1.5 py-0.5 text-[10px] bg-blue-500/20 text-blue-300 rounded flex-shrink-0">
                Shared
              </span>
            )}
          </div>
          {kb.description && (
            <p className="text-xs text-slate-400 mb-1.5 line-clamp-1">{kb.description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={onDelete}
            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
            title="Delete"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-2 text-xs">
        <div className="flex items-center gap-1.5 text-slate-400">
          <FileText className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">{kb.file_count} files</span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-400">
          <Database className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">{kb.vector_count.toLocaleString()} vectors</span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-400">
          <Tag className="w-3 h-3 flex-shrink-0" />
          <span>v{kb.current_version}</span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-400">
          <Clock className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">{new Date(kb.updated_at).toLocaleDateString()}</span>
        </div>
      </div>

      {/* Processing Status */}
      {status && (
        <div className={cn(
          'flex items-center gap-1.5 px-2 py-1 rounded text-xs mb-2 border',
          status === 'completed' && 'text-green-400 bg-green-500/10 border-green-500/20',
          status === 'processing' && 'text-blue-400 bg-blue-500/10 border-blue-500/20',
          status === 'failed' && 'text-red-400 bg-red-500/10 border-red-500/20',
          status === 'pending' && 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
        )}>
          {status === 'completed' && <CheckCircle className="w-3 h-3" />}
          {status === 'processing' && <Loader2 className="w-3 h-3 animate-spin" />}
          {status === 'failed' && <AlertCircle className="w-3 h-3" />}
          {status === 'pending' && <Clock className="w-3 h-3" />}
          <span className="capitalize">{status}</span>
        </div>
      )}

      <div className="flex items-center gap-1.5 pt-2 border-t border-white/10">
        <button
          onClick={onManage}
          className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 rounded transition-colors"
          title="View Details"
        >
          <Settings className="w-3 h-3" />
          <span>Manage</span>
        </button>
        <button
          onClick={onProcess}
          className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs bg-green-600/20 hover:bg-green-600/30 text-green-300 rounded transition-colors"
          title="Process Files"
        >
          <Play className="w-3 h-3" />
          <span>Process</span>
        </button>
      </div>
    </div>
  );
}

export function KnowledgeBaseManager() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseListItem[]>([]);
  const [kbStatuses, setKbStatuses] = useState<Record<string, ProcessingStatus | null>>({});
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKBName, setNewKBName] = useState('');
  const [newKBDescription, setNewKBDescription] = useState('');
  const [selectedKBId, setSelectedKBId] = useState<string | null>(null);
  const [processingKBId, setProcessingKBId] = useState<string | null>(null);

  useEffect(() => {
    loadKnowledgeBases(true); // Initial load with loading indicator
    // Auto-refresh every 3 seconds to check processing status (silent)
    const interval = setInterval(() => loadKnowledgeBases(false), 3000);
    return () => clearInterval(interval);
  }, []);

  const loadKnowledgeBases = async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const response = await listKnowledgeBases();
      const safeKnowledgeBases = response?.knowledge_bases || [];
      setKnowledgeBases(safeKnowledgeBases);
      
      // Fetch statuses for all knowledge bases
      const statusPromises = safeKnowledgeBases.map(async (kb) => {
        try {
          const fullKB = await getKnowledgeBase(kb.id);
          const currentVersion = fullKB.versions.find((v) => v.version_number === fullKB.current_version);
          return { id: kb.id, status: currentVersion?.status || null };
        } catch {
          return { id: kb.id, status: null };
        }
      });
      
      const statusResults = await Promise.all(statusPromises);
      const statusMap: Record<string, ProcessingStatus | null> = {};
      statusResults.forEach(({ id, status }) => {
        statusMap[id] = status;
      });
      setKbStatuses(statusMap);
    } catch (error: any) {
      console.error('Error loading knowledge bases:', error);
      if (showLoading) {
        toast.error('Failed to load knowledge bases');
      }
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const handleCreateKB = async () => {
    if (!newKBName.trim()) {
      toast.error('Please enter a name for the knowledge base');
      return;
    }

    try {
      const request: CreateKnowledgeBaseRequest = {
        name: newKBName.trim(),
        description: newKBDescription.trim() || undefined,
        tags: [],
        is_shared: false,
      };

      await createKnowledgeBase(request);
      toast.success(`Knowledge base "${newKBName}" created`);
      setNewKBName('');
      setNewKBDescription('');
      setShowCreateModal(false);
      loadKnowledgeBases(true);
    } catch (error: any) {
      console.error('Error creating knowledge base:', error);
      toast.error(error.response?.data?.detail?.message || error.message || 'Failed to create knowledge base');
    }
  };

  const handleDeleteKB = async (kbId: string, kbName: string) => {
    if (!window.confirm(`Are you sure you want to delete "${kbName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await deleteKnowledgeBase(kbId);
      toast.success('Knowledge base deleted');
      loadKnowledgeBases(true);
    } catch (error: any) {
      console.error('Error deleting knowledge base:', error);
      toast.error(error.response?.data?.detail?.message || error.message || 'Failed to delete knowledge base');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p>Loading knowledge bases...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-y-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between flex-shrink-0">
        <div>
          <h3 className="text-lg font-semibold text-white">Knowledge Bases</h3>
          <p className="text-sm text-slate-400 mt-1">
            Manage your document collections and processing configurations
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Knowledge Base</span>
        </button>
      </div>

      {/* Knowledge Bases List */}
      <div className="flex-1 overflow-y-auto p-6">
        {knowledgeBases.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <Database className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg mb-2">No knowledge bases yet</p>
            <p className="text-sm mb-6">Create your first knowledge base to get started</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Create Knowledge Base</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {knowledgeBases.map((kb) => (
              <KnowledgeBaseCard
                key={kb.id}
                kb={kb}
                status={kbStatuses[kb.id]}
                onManage={() => setSelectedKBId(kb.id)}
                onProcess={() => setProcessingKBId(kb.id)}
                onDelete={() => handleDeleteKB(kb.id, kb.name)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <>
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
            onClick={() => setShowCreateModal(false)}
          />
          <div className="fixed inset-0 z-[101] flex items-center justify-center p-4">
            <div
              className="bg-slate-800 border border-white/10 rounded-lg shadow-2xl w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-white/10">
                <h3 className="text-lg font-semibold text-white">Create Knowledge Base</h3>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={newKBName}
                    onChange={(e) => setNewKBName(e.target.value)}
                    placeholder="My Knowledge Base"
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCreateKB();
                      if (e.key === 'Escape') setShowCreateModal(false);
                    }}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Description
                  </label>
                  <textarea
                    value={newKBDescription}
                    onChange={(e) => setNewKBDescription(e.target.value)}
                    placeholder="Optional description..."
                    rows={3}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                  />
                </div>
              </div>
              <div className="p-6 border-t border-white/10 flex items-center justify-end gap-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateKB}
                  className="px-4 py-2 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded transition-colors"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Knowledge Base Detail Modal */}
      {selectedKBId && (
        <div className="fixed inset-0 z-[100] flex">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setSelectedKBId(null)}
          />
          <div className="fixed right-0 top-0 bottom-0 w-[600px] bg-slate-900/98 backdrop-blur-lg border-l border-white/10 shadow-2xl z-[101]">
            <KnowledgeBaseDetail
              kbId={selectedKBId}
              onClose={() => setSelectedKBId(null)}
              onRefresh={loadKnowledgeBases}
            />
          </div>
        </div>
      )}

      {/* Process Knowledge Base Modal */}
      {processingKBId && (
        <ProcessKnowledgeBaseModal
          kbId={processingKBId}
          isOpen={!!processingKBId}
          onClose={() => setProcessingKBId(null)}
          onProcessed={() => {
            loadKnowledgeBases(true);
            setProcessingKBId(null);
          }}
        />
      )}
    </div>
  );
}

