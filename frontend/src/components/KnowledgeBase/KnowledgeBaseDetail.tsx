/**
 * Enhanced Knowledge Base Detail View
 * 
 * Features:
 * - Version history with rollback
 * - Version comparison with diff view
 * - Configuration details
 * - Reprocessing workflows
 */

import { useState, useEffect } from 'react';
import { 
  X, Clock, CheckCircle, AlertCircle, Loader2, 
  GitBranch, RotateCcw, GitCompare, ChevronDown, ChevronRight,
  FileText, Layers, Database, Settings
} from 'lucide-react';
import { cn } from '@/utils/cn';
import {
  getKnowledgeBase,
  listKnowledgeBaseVersions,
  compareVersions,
  rollbackToVersion,
  type KnowledgeBase,
  type KnowledgeBaseVersion,
  type ProcessingStatus,
  type VersionComparison,
} from '@/services/knowledgeBase';
import toast from 'react-hot-toast';

interface KnowledgeBaseDetailProps {
  kbId: string;
  onClose: () => void;
  onRefresh?: () => void;
}

type ViewMode = 'versions' | 'compare';

export function KnowledgeBaseDetail({ kbId, onClose, onRefresh }: KnowledgeBaseDetailProps) {
  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [loading, setLoading] = useState(true);
  const [versions, setVersions] = useState<KnowledgeBaseVersion[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('versions');
  const [selectedVersion1, setSelectedVersion1] = useState<number | null>(null);
  const [selectedVersion2, setSelectedVersion2] = useState<number | null>(null);
  const [comparison, setComparison] = useState<VersionComparison | null>(null);
  const [expandedVersions, setExpandedVersions] = useState<Set<number>>(new Set());
  const [loadingComparison, setLoadingComparison] = useState(false);

  useEffect(() => {
    loadKB();
    const interval = setInterval(loadKB, 2000); // Refresh every 2 seconds to check processing status
    return () => clearInterval(interval);
  }, [kbId]);

  const loadKB = async () => {
    try {
      const [kbData, versionsData] = await Promise.all([
        getKnowledgeBase(kbId),
        listKnowledgeBaseVersions(kbId),
      ]);
      setKb(kbData);
      setVersions(versionsData.sort((a, b) => b.version_number - a.version_number));
      if (loading) setLoading(false);
    } catch (error: any) {
      console.error('Error loading knowledge base:', error);
      toast.error('Failed to load knowledge base details');
      if (loading) setLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!selectedVersion1 || !selectedVersion2) {
      toast.error('Please select two versions to compare');
      return;
    }

    setLoadingComparison(true);
    try {
      const comp = await compareVersions(kbId, selectedVersion1, selectedVersion2);
      setComparison(comp);
      setViewMode('compare');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to compare versions');
    } finally {
      setLoadingComparison(false);
    }
  };

  const handleRollback = async (versionNumber: number) => {
    if (!confirm(`Rollback to version ${versionNumber}? This will make it the current version.`)) {
      return;
    }

    try {
      await rollbackToVersion(kbId, versionNumber);
      toast.success(`Rolled back to version ${versionNumber}`);
      loadKB();
      if (onRefresh) onRefresh();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to rollback');
    }
  };

  const toggleVersionExpanded = (versionNumber: number) => {
    const newExpanded = new Set(expandedVersions);
    if (newExpanded.has(versionNumber)) {
      newExpanded.delete(versionNumber);
    } else {
      newExpanded.add(versionNumber);
    }
    setExpandedVersions(newExpanded);
  };

  const getStatusIcon = (status: ProcessingStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusColor = (status: ProcessingStatus) => {
    switch (status) {
      case 'completed':
        return 'text-green-400 bg-green-500/10 border-green-500/20';
      case 'processing':
        return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
      case 'failed':
        return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'pending':
        return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      default:
        return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mr-2" />
        <span>Loading knowledge base...</span>
      </div>
    );
  }

  if (!kb) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        <p>Knowledge base not found</p>
      </div>
    );
  }

  const currentVersion = versions.find((v) => v.version_number === kb.current_version);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between flex-shrink-0">
        <div>
          <h3 className="text-lg font-semibold text-white">{kb.name}</h3>
          {kb.description && (
            <p className="text-sm text-slate-400 mt-1">{kb.description}</p>
          )}
        </div>
        <button
          onClick={onClose}
          className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/10 flex-shrink-0">
        <button
          onClick={() => setViewMode('versions')}
          className={cn(
            'px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2',
            viewMode === 'versions'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-slate-400 hover:text-slate-300'
          )}
        >
          <GitBranch className="w-4 h-4" />
          Versions
        </button>
        <button
          onClick={() => setViewMode('compare')}
          className={cn(
            'px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2',
            viewMode === 'compare'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-slate-400 hover:text-slate-300'
          )}
        >
          <GitCompare className="w-4 h-4" />
          Compare
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {viewMode === 'versions' ? (
          <VersionsView
            kb={kb}
            versions={versions}
            currentVersion={currentVersion}
            expandedVersions={expandedVersions}
            onToggleExpanded={toggleVersionExpanded}
            onRollback={handleRollback}
            getStatusIcon={getStatusIcon}
            getStatusColor={getStatusColor}
          />
        ) : (
          <CompareView
            versions={versions}
            selectedVersion1={selectedVersion1}
            selectedVersion2={selectedVersion2}
            onSelectVersion1={setSelectedVersion1}
            onSelectVersion2={setSelectedVersion2}
            onCompare={handleCompare}
            comparison={comparison}
            loadingComparison={loadingComparison}
            currentVersion={kb.current_version}
          />
        )}
      </div>
    </div>
  );
}

function VersionsView({
  kb,
  versions,
  currentVersion,
  expandedVersions,
  onToggleExpanded,
  onRollback,
  getStatusIcon,
  getStatusColor,
}: {
  kb: KnowledgeBase;
  versions: KnowledgeBaseVersion[];
  currentVersion?: KnowledgeBaseVersion;
  expandedVersions: Set<number>;
  onToggleExpanded: (versionNumber: number) => void;
  onRollback: (versionNumber: number) => void;
  getStatusIcon: (status: ProcessingStatus) => React.ReactElement;
  getStatusColor: (status: ProcessingStatus) => string;
}) {
  return (
    <div className="space-y-4">
      {/* Current Version Summary */}
      {currentVersion && (
        <div className="glass rounded-lg p-4 border border-purple-500/50 bg-purple-500/10">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-white flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-purple-400" />
              Current Version: v{currentVersion.version_number}
            </h4>
            <div className={cn('flex items-center gap-2 px-2 py-1 rounded border', getStatusColor(currentVersion.status))}>
              {getStatusIcon(currentVersion.status)}
              <span className="text-xs font-medium capitalize">{currentVersion.status}</span>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-slate-400">Files:</span>
              <span className="text-white ml-2 font-semibold">{currentVersion.file_ids.length}</span>
            </div>
            <div>
              <span className="text-slate-400">Vectors:</span>
              <span className="text-white ml-2 font-semibold">{currentVersion.vector_count.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-slate-400">Cost:</span>
              <span className="text-white ml-2 font-semibold">${currentVersion.total_cost.toFixed(4)}</span>
            </div>
            {currentVersion.processing_duration_ms && (
              <div>
                <span className="text-slate-400">Duration:</span>
                <span className="text-white ml-2 font-semibold">
                  {currentVersion.processing_duration_ms > 1000
                    ? `${(currentVersion.processing_duration_ms / 1000).toFixed(1)}s`
                    : `${currentVersion.processing_duration_ms}ms`}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Version History */}
      <div>
        <h4 className="font-semibold text-white mb-3">Version History</h4>
        <div className="space-y-2">
          {versions.map((version) => {
            const isExpanded = expandedVersions.has(version.version_number);
            const isCurrent = version.version_number === kb.current_version;
            const canRollback = version.status === 'completed' && !isCurrent;

            return (
              <div
                key={version.id}
                className={cn(
                  'glass rounded-lg border overflow-hidden',
                  isCurrent
                    ? 'border-purple-500/50 bg-purple-500/5'
                    : 'border-white/10'
                )}
              >
                {/* Version Header */}
                <button
                  onClick={() => onToggleExpanded(version.version_number)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                    <span className="font-medium text-white">v{version.version_number}</span>
                    <div className={cn('flex items-center gap-1.5 px-2 py-0.5 rounded border text-xs', getStatusColor(version.status))}>
                      {getStatusIcon(version.status)}
                      <span className="capitalize">{version.status}</span>
                    </div>
                    {isCurrent && (
                      <span className="text-xs text-purple-400 font-medium">(Current)</span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span>{new Date(version.created_at).toLocaleString()}</span>
                    {canRollback && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRollback(version.version_number);
                        }}
                        className="px-2 py-1 text-yellow-400 hover:text-yellow-300 hover:bg-yellow-500/10 rounded transition-colors flex items-center gap-1"
                        title="Rollback to this version"
                      >
                        <RotateCcw className="w-3 h-3" />
                        Rollback
                      </button>
                    )}
                  </div>
                </button>

                {/* Version Details */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-white/10 pt-3 space-y-3">
                    {/* Configuration Details */}
                    <div className="grid grid-cols-3 gap-4">
                      {/* Chunk Config */}
                      <div className="bg-white/5 rounded p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <FileText className="w-4 h-4 text-blue-400" />
                          <span className="text-xs font-semibold text-slate-300">Chunking</span>
                        </div>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-400">Size:</span>
                            <span className="text-white">{version.chunk_config.chunk_size}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Overlap:</span>
                            <span className="text-white">{version.chunk_config.chunk_overlap}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Strategy:</span>
                            <span className="text-white capitalize">{version.chunk_config.strategy}</span>
                          </div>
                        </div>
                      </div>

                      {/* Embed Config */}
                      <div className="bg-white/5 rounded p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <Layers className="w-4 h-4 text-purple-400" />
                          <span className="text-xs font-semibold text-slate-300">Embedding</span>
                        </div>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-400">Provider:</span>
                            <span className="text-white capitalize">{version.embed_config.provider}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Model:</span>
                            <span className="text-white truncate ml-2" title={version.embed_config.model}>
                              {version.embed_config.model}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Vector Store Config */}
                      <div className="bg-white/5 rounded p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <Database className="w-4 h-4 text-green-400" />
                          <span className="text-xs font-semibold text-slate-300">Vector Store</span>
                        </div>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-400">Provider:</span>
                            <span className="text-white capitalize">{version.vector_store_config.provider}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Type:</span>
                            <span className="text-white capitalize">{version.vector_store_config.index_type}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-4 gap-3 text-sm">
                      <div>
                        <div className="text-slate-400 mb-1">Files</div>
                        <div className="text-white font-semibold">{version.file_ids.length}</div>
                      </div>
                      <div>
                        <div className="text-slate-400 mb-1">Vectors</div>
                        <div className="text-white font-semibold">{version.vector_count.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-slate-400 mb-1">Cost</div>
                        <div className="text-white font-semibold">${version.total_cost.toFixed(4)}</div>
                      </div>
                      {version.processing_duration_ms && (
                        <div>
                          <div className="text-slate-400 mb-1">Duration</div>
                          <div className="text-white font-semibold">
                            {version.processing_duration_ms > 1000
                              ? `${(version.processing_duration_ms / 1000).toFixed(1)}s`
                              : `${version.processing_duration_ms}ms`}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Processing Log */}
                    {version.processing_log && (
                      <div className="bg-black/20 rounded p-2">
                        <div className="text-xs text-slate-400 mb-1">Processing Log</div>
                        <div className="text-xs text-slate-300 whitespace-pre-wrap">{version.processing_log}</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function CompareView({
  versions,
  selectedVersion1,
  selectedVersion2,
  onSelectVersion1,
  onSelectVersion2,
  onCompare,
  comparison,
  loadingComparison,
  currentVersion,
}: {
  versions: KnowledgeBaseVersion[];
  selectedVersion1: number | null;
  selectedVersion2: number | null;
  onSelectVersion1: (version: number | null) => void;
  onSelectVersion2: (version: number | null) => void;
  onCompare: () => void;
  comparison: VersionComparison | null;
  loadingComparison: boolean;
  currentVersion: number;
}) {
  return (
    <div className="space-y-4">
      {/* Version Selectors */}
      <div className="glass rounded-lg p-4 border border-white/10">
        <h4 className="font-semibold text-white mb-4">Select Versions to Compare</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-400 mb-2">Version 1</label>
            <select
              value={selectedVersion1 || ''}
              onChange={(e) => onSelectVersion1(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">Select version...</option>
              {versions.map((v) => (
                <option key={v.version_number} value={v.version_number}>
                  v{v.version_number} {v.version_number === currentVersion && '(Current)'}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-2">Version 2</label>
            <select
              value={selectedVersion2 || ''}
              onChange={(e) => onSelectVersion2(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">Select version...</option>
              {versions.map((v) => (
                <option key={v.version_number} value={v.version_number}>
                  v{v.version_number} {v.version_number === currentVersion && '(Current)'}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          onClick={onCompare}
          disabled={!selectedVersion1 || !selectedVersion2 || loadingComparison}
          className="mt-4 w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loadingComparison ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Comparing...
            </>
          ) : (
            <>
              <GitCompare className="w-4 h-4" />
              Compare Versions
            </>
          )}
        </button>
      </div>

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-4">
          <div className="glass rounded-lg p-4 border border-white/10">
            <h4 className="font-semibold text-white mb-4">Comparison Results</h4>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-xs text-slate-400 mb-1">Version {comparison.version1.version_number}</div>
                <div className="text-sm text-white">
                  {new Date(comparison.version1.created_at).toLocaleString()}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-400 mb-1">Version {comparison.version2.version_number}</div>
                <div className="text-sm text-white">
                  {new Date(comparison.version2.created_at).toLocaleString()}
                </div>
              </div>
            </div>

            {/* Differences */}
            {Object.keys(comparison.differences).length === 0 ? (
              <div className="text-center py-4 text-slate-400 text-sm">
                No differences found between these versions
              </div>
            ) : (
              <div className="space-y-3">
                {/* Chunk Config Differences */}
                {comparison.differences.chunk_config && (
                  <div className="bg-white/5 rounded p-3 border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-4 h-4 text-blue-400" />
                      <span className="text-sm font-semibold text-white">Chunking Configuration</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      {Object.entries(comparison.differences.chunk_config).map(([key, diff]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-slate-400 capitalize">{key.replace('_', ' ')}:</span>
                          <div className="flex items-center gap-2">
                            <span className="text-red-400 line-through">{diff.v1}</span>
                            <span className="text-slate-500">→</span>
                            <span className="text-green-400">{diff.v2}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Embed Config Differences */}
                {comparison.differences.embed_config && (
                  <div className="bg-white/5 rounded p-3 border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <Layers className="w-4 h-4 text-purple-400" />
                      <span className="text-sm font-semibold text-white">Embedding Configuration</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      {Object.entries(comparison.differences.embed_config).map(([key, diff]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-slate-400 capitalize">{key}:</span>
                          <div className="flex items-center gap-2">
                            <span className="text-red-400 line-through">{diff.v1}</span>
                            <span className="text-slate-500">→</span>
                            <span className="text-green-400">{diff.v2}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Vector Store Config Differences */}
                {comparison.differences.vector_store_config && (
                  <div className="bg-white/5 rounded p-3 border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <Database className="w-4 h-4 text-green-400" />
                      <span className="text-sm font-semibold text-white">Vector Store Configuration</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      {Object.entries(comparison.differences.vector_store_config).map(([key, diff]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-slate-400 capitalize">{key.replace('_', ' ')}:</span>
                          <div className="flex items-center gap-2">
                            <span className="text-red-400 line-through">{diff.v1}</span>
                            <span className="text-slate-500">→</span>
                            <span className="text-green-400">{diff.v2}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Files Differences */}
                {comparison.differences.files && (
                  <div className="bg-white/5 rounded p-3 border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-4 h-4 text-yellow-400" />
                      <span className="text-sm font-semibold text-white">Files</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Count:</span>
                        <div className="flex items-center gap-2">
                          <span className="text-red-400">{comparison.differences.files.v1_count}</span>
                          <span className="text-slate-500">→</span>
                          <span className="text-green-400">{comparison.differences.files.v2_count}</span>
                        </div>
                      </div>
                      {comparison.differences.files.added.length > 0 && (
                        <div>
                          <span className="text-green-400">+{comparison.differences.files.added.length} added</span>
                        </div>
                      )}
                      {comparison.differences.files.removed.length > 0 && (
                        <div>
                          <span className="text-red-400">-{comparison.differences.files.removed.length} removed</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Metadata Differences */}
                {comparison.differences.metadata && (
                  <div className="bg-white/5 rounded p-3 border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <Settings className="w-4 h-4 text-slate-400" />
                      <span className="text-sm font-semibold text-white">Metadata</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      {Object.entries(comparison.differences.metadata).map(([key, diff]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-slate-400 capitalize">{key.replace('_', ' ')}:</span>
                          <div className="flex items-center gap-2">
                            <span className="text-red-400 line-through">
                              {key === 'total_cost' ? `$${diff.v1.toFixed(4)}` : diff.v1.toLocaleString()}
                            </span>
                            <span className="text-slate-500">→</span>
                            <span className="text-green-400">
                              {key === 'total_cost' ? `$${diff.v2.toFixed(4)}` : diff.v2.toLocaleString()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
