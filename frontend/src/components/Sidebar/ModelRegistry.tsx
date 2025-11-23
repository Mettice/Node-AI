/**
 * Model Registry Panel - displays fine-tuned models
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  GraduationCap, 
  Search, 
  Trash2, 
  ExternalLink,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  DollarSign,
  Calendar,
  MessageSquare,
  Brain,
} from 'lucide-react';
import { listModels, deleteModel, type FineTunedModel } from '@/services/models';
import { Spinner } from '@/components/common/Spinner';
import { cn } from '@/utils/cn';
import { useWorkflowStore } from '@/store/workflowStore';
import { useUIStore } from '@/store/uiStore';
import toast from 'react-hot-toast';

export function ModelRegistry() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const queryClient = useQueryClient();

  // Fetch models
  const { data: models = [], isLoading, error } = useQuery({
    queryKey: ['models', statusFilter],
    queryFn: () => listModels({ status: statusFilter !== 'all' ? statusFilter : undefined }),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (modelId: string) => deleteModel(modelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });

  // Filter models by search
  const filteredModels = models.filter((model) => {
    const matchesSearch =
      model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.base_model.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case 'training':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'failed':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'training':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-red-400 mb-2">Failed to load models</p>
          <p className="text-sm text-slate-400">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col glass-strong border-r border-white/10">
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center gap-2 mb-3">
          <GraduationCap className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold text-white">Model Registry</h2>
        </div>

        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search models..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all text-sm"
          />
        </div>

        {/* Status Filter */}
        <div className="flex gap-2">
          {['all', 'ready', 'training', 'failed'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={cn(
                'px-3 py-1 rounded-md text-xs font-medium transition-all',
                statusFilter === status
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                  : 'bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10'
              )}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Models List */}
      <div className="flex-1 overflow-y-auto p-2">
        {filteredModels.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            <GraduationCap className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No models found</p>
            {searchQuery && (
              <p className="text-xs mt-1">Try a different search term</p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredModels.map((model) => (
              <ModelCard
                key={model.id}
                model={model}
                onDelete={() => deleteMutation.mutate(model.id)}
                getStatusIcon={getStatusIcon}
                getStatusColor={getStatusColor}
                formatDate={formatDate}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface DeployButtonProps {
  model: FineTunedModel;
}

function DeployButton({ model }: DeployButtonProps) {
  const { nodes, updateNode } = useWorkflowStore();
  const { setSidebarTab } = useUIStore();
  const [showDeployMenu, setShowDeployMenu] = useState(false);

  const handleDeploy = (nodeType: 'chat' | 'embed') => {
    // Find nodes of the specified type
    const targetNodes = nodes.filter((n) => n.type === nodeType);
    
    if (targetNodes.length === 0) {
      toast.error(`No ${nodeType} nodes found. Add a ${nodeType} node to the canvas first.`);
      return;
    }

    // Update the first matching node (or could show a selector for multiple)
    const nodeToUpdate = targetNodes[0];
    const currentConfig = nodeToUpdate.data.config || {};
    
    updateNode(nodeToUpdate.id, {
      ...nodeToUpdate.data,
      config: {
        ...currentConfig,
        use_finetuned_model: true,
        finetuned_model_id: model.id,
        // Ensure provider matches
        provider: model.provider,
      },
    });

    toast.success(`Deployed ${model.name} to ${nodeType} node`);
    setShowDeployMenu(false);
    // Switch to nodes tab to see the updated node
    setSidebarTab('nodes');
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowDeployMenu(!showDeployMenu)}
        className="px-3 py-1.5 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded hover:bg-purple-500/30 transition-all text-xs font-medium flex items-center gap-1"
      >
        <ExternalLink className="w-3 h-3" />
        Deploy to Node
      </button>
      
      {showDeployMenu && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowDeployMenu(false)}
          />
          <div className="absolute top-full left-0 mt-1 bg-slate-800 border border-white/10 rounded-lg shadow-xl z-20 min-w-[180px]">
            <button
              onClick={() => handleDeploy('chat')}
              className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-2 transition-colors"
            >
              <MessageSquare className="w-4 h-4" />
              Deploy to Chat Node
            </button>
            <button
              onClick={() => handleDeploy('embed')}
              className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-2 transition-colors border-t border-white/10"
            >
              <Brain className="w-4 h-4" />
              Deploy to Embed Node
            </button>
          </div>
        </>
      )}
    </div>
  );
}

interface ModelCardProps {
  model: FineTunedModel;
  onDelete: () => void;
  getStatusIcon: (status: string) => React.ReactNode;
  getStatusColor: (status: string) => string;
  formatDate: (date: string) => string;
}

function ModelCard({ model, onDelete, getStatusIcon, getStatusColor, formatDate }: ModelCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="glass-light rounded-lg border border-white/10 p-3 hover:border-purple-500/30 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-white text-sm truncate">{model.name}</h3>
            <div className={cn('flex items-center gap-1 px-2 py-0.5 rounded text-xs border', getStatusColor(model.status))}>
              {getStatusIcon(model.status)}
              <span className="capitalize">{model.status}</span>
            </div>
          </div>
          <p className="text-xs text-slate-400 truncate">{model.base_model}</p>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-slate-400 hover:text-white transition-colors"
        >
          <ExternalLink className={cn('w-4 h-4 transition-transform', isExpanded && 'rotate-90')} />
        </button>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
        {model.usage_count > 0 && (
          <div className="flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            <span>{model.usage_count} uses</span>
          </div>
        )}
        {model.estimated_cost && (
          <div className="flex items-center gap-1">
            <DollarSign className="w-3 h-3" />
            <span>${model.estimated_cost.toFixed(2)}</span>
          </div>
        )}
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          <span>{formatDate(model.created_at)}</span>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-white/10 space-y-2 text-xs">
          {model.description && (
            <div>
              <span className="text-slate-400">Description: </span>
              <span className="text-slate-300">{model.description}</span>
            </div>
          )}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-slate-400">Provider: </span>
              <span className="text-slate-300 capitalize">{model.provider}</span>
            </div>
            <div>
              <span className="text-slate-400">Epochs: </span>
              <span className="text-slate-300">{model.epochs}</span>
            </div>
            <div>
              <span className="text-slate-400">Training Examples: </span>
              <span className="text-slate-300">{model.training_examples.toLocaleString()}</span>
            </div>
            {model.validation_examples && (
              <div>
                <span className="text-slate-400">Validation Examples: </span>
                <span className="text-slate-300">{model.validation_examples.toLocaleString()}</span>
              </div>
            )}
          </div>
          <div className="pt-2 flex gap-2">
            <button
              onClick={onDelete}
              className="px-3 py-1.5 bg-red-500/20 text-red-400 border border-red-500/30 rounded hover:bg-red-500/30 transition-all text-xs font-medium flex items-center gap-1"
            >
              <Trash2 className="w-3 h-3" />
              Delete
            </button>
            <DeployButton model={model} />
          </div>
        </div>
      )}
    </div>
  );
}

