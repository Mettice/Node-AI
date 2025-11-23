/**
 * Node card component - individual node in the palette
 * Dark glassmorphic theme with category glows
 */

import { 
  FileText, 
  Scissors, 
  Brain, 
  Database, 
  Search, 
  MessageSquare,
  GripVertical,
  Upload,
  Scan,
  Mic,
  Video,
  Table,
  FileSpreadsheet,
  Eye,
  BrainCircuit,
  Bot,
  Wrench,
  Users,
  GraduationCap,
  Cloud,
  Mail,
  Network,
} from 'lucide-react';
import { NODE_CATEGORY_COLORS } from '@/constants';
import type { NodeMetadata } from '@/types/node';
import { cn } from '@/utils/cn';
import { ProviderIcon } from '@/components/common/ProviderIcon';

// Icon mapping
const nodeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  text_input: FileText,
  file_loader: Upload,
  chunk: Scissors,
  ocr: Scan,
  transcribe: Mic,
  video_frames: Video,
  data_loader: FileSpreadsheet,
  data_to_text: Table,
  embed: Brain,
  vector_store: Database,
  vector_search: Search,
  rerank: Search, // Use Search icon with different styling
  hybrid_retrieval: Search, // Hybrid retrieval combines vector + graph
  knowledge_graph: Network, // Network icon for knowledge graph
  chat: MessageSquare,
  vision: Eye,
  memory: BrainCircuit,
  langchain_agent: Bot, // Will be replaced with ProviderIcon
  tool: Wrench,
  crewai_agent: Users, // Will be replaced with ProviderIcon
  s3: Cloud, // Will be replaced with ProviderIcon
  email: Mail, // Will be replaced with ProviderIcon
  database: Database, // Will be replaced with ProviderIcon
  slack: MessageSquare, // Will be replaced with ProviderIcon
  google_drive: Cloud, // Will be replaced with ProviderIcon
  reddit: MessageSquare, // Will be replaced with ProviderIcon
  finetune: GraduationCap,
};

interface NodeCardProps {
  node: NodeMetadata;
}

export function NodeCard({ node }: NodeCardProps) {
  const category = node.category || 'default';
  const categoryColor = NODE_CATEGORY_COLORS[category as keyof typeof NODE_CATEGORY_COLORS] || '#9ca3af';
  
  // Use ProviderIcon for nodes that have provider-specific icons
  const getProviderIconName = (nodeType: string): string | null => {
    const providerIconMap: Record<string, string> = {
      'crewai_agent': 'crewai',
      'langchain_agent': 'langchain',
      's3': 's3',
      'email': 'resend',
      'database': 'sqlite', // Default to sqlite icon in palette
      'slack': 'slack',
      'google_drive': 'googledrive',
      'reddit': 'reddit',
    };
    return providerIconMap[nodeType] || null;
  };

  const providerIconName = getProviderIconName(node.type);
  const useProviderIcon = providerIconName !== null;
  const Icon = useProviderIcon ? null : (nodeIcons[node.type] || FileText);

  // Handle node drag
  const handleDragStart = (e: React.DragEvent) => {
    // Prevent child elements from interfering
    e.stopPropagation();
    
    const nodeData = {
      label: node.name,
      category: node.category,
      status: 'idle' as const,
      config: {},
    };

    const dragData = JSON.stringify({
      type: node.type,
      data: nodeData,
    });

    // Set data with both the custom type and text/plain as fallback
    e.dataTransfer.setData('application/reactflow', dragData);
    e.dataTransfer.setData('text/plain', dragData); // Fallback for some browsers
    e.dataTransfer.effectAllowed = 'move';
  };

  // Get glow class based on category
  const getGlowClass = () => {
    const glowMap: Record<string, string> = {
      input: 'glow-input',
      processing: 'glow-processing',
      embedding: 'glow-embedding',
      storage: 'glow-storage',
      retrieval: 'glow-retrieval',
      llm: 'glow-llm',
      tool: 'glow-storage', // Use storage glow for tools
      memory: 'glow-llm', // Use llm glow for memory
      agent: 'glow-processing', // Use processing glow for agents
    };
    return glowMap[category] || '';
  };

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      className={cn(
        'flex items-center gap-3 px-3 py-2.5 rounded-lg',
        'glass-light glass-shine',
        'cursor-move transition-all duration-300 ease-out',
        'hover:scale-[1.02] hover:-translate-y-0.5',
        'group relative'
      )}
      style={{
        borderLeft: `3px solid ${categoryColor}`,
        boxShadow: `
          0 4px 6px rgba(0, 0, 0, 0.2),
          inset 0 1px 0 rgba(255, 255, 255, 0.05)
        `,
      }}
      onMouseEnter={(e) => {
        const glowClass = getGlowClass();
        if (glowClass) {
          e.currentTarget.classList.add(glowClass);
        }
      }}
      onMouseLeave={(e) => {
        const glowClass = getGlowClass();
        if (glowClass) {
          e.currentTarget.classList.remove(glowClass);
        }
      }}
      title={node.description}
    >
      <div 
        draggable={false}
        onDragStart={(e) => e.preventDefault()}
        className="flex-shrink-0"
      >
        <GripVertical className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300 transition-colors" />
      </div>
      
      <div 
        className="p-2 rounded-lg transition-all duration-300 group-hover:scale-110 flex-shrink-0"
        style={{ 
          backgroundColor: `${categoryColor}20`,
          boxShadow: `0 0 10px ${categoryColor}30`,
          color: categoryColor
        }}
        draggable={false}
        onDragStart={(e) => e.preventDefault()}
      >
        {useProviderIcon && providerIconName ? (
          <ProviderIcon provider={providerIconName} size="sm" />
        ) : (
          Icon && <Icon className="w-3.5 h-3.5" />
        )}
      </div>
      
      <span 
        className="text-sm font-medium text-slate-200 flex-1"
        draggable={false}
        onDragStart={(e) => e.preventDefault()}
      >
        {node.name}
      </span>
    </div>
  );
}
