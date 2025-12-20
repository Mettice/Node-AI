/**
 * Unified Node Output Display Component
 * 
 * This component provides consistent rendering for all node types based on
 * standardized display metadata from the backend formatter system.
 */

import React from 'react';
import { Copy, Download, FileText, BarChart3, Code, AlertCircle } from 'lucide-react';
import { cn } from '@/utils/cn';

interface DisplayMetadata {
  display_type: 'text' | 'html' | 'chart' | 'data' | 'agent_report' | 'empty';
  primary_content: any;
  metadata: {
    node_type: string;
    [key: string]: any;
  };
  actions: string[];
  attachments: Array<{
    type: string;
    name: string;
    data: string;
    mime_type: string;
  }>;
}

interface NodeOutput {
  _display_metadata?: DisplayMetadata;
  [key: string]: any;
}

interface UnifiedNodeOutputProps {
  nodeId: string;
  nodeType: string;
  nodeName: string;
  output: NodeOutput;
  isExpanded?: boolean;
  categoryColor?: string;
  className?: string;
}

export function UnifiedNodeOutput({
  nodeId,
  nodeType,
  nodeName,
  output,
  isExpanded = true,
  categoryColor = '#9ca3af',
  className
}: UnifiedNodeOutputProps) {
  const displayMetadata = output._display_metadata;
  
  if (!displayMetadata) {
    return <FallbackDisplay nodeType={nodeType} output={output} className={className} />;
  }
  
  // Since primary_content is not included in metadata to avoid circular refs,
  // we need to reconstruct it from the original output based on display type
  const getPrimaryContent = () => {
    switch (displayMetadata.display_type) {
      case 'text':
        // Extract text content from various possible fields
        return output.output || output.text || output.content || output.summary || '';
      
      case 'html':
        // For HTML content, we need to format it (this should be done by the formatter)
        // For now, return structured content
        if (output.blog_post) {
          return output; // Let the HTML renderer handle the full blog_post structure
        }
        return output.output || output.content || '';
      
      case 'chart':
        // Return chart data
        return {
          charts: output.charts || output.visual_charts || [],
          summary: output.data_summary || {},
          metadata: output.metadata || {}
        };
      
      case 'agent_report':
        // Return agent data
        return {
          summary: output.output || '',
          agent_outputs: output.agent_outputs || {},
          agents: output.agents || []
        };
      
      case 'data':
      default:
        return output;
    }
  };
  
  // Create enhanced metadata with reconstructed primary content
  const enhancedMetadata = {
    ...displayMetadata,
    primary_content: getPrimaryContent()
  };
  
  const handleAction = (action: string) => {
    switch (action) {
      case 'copy':
        const textToCopy = typeof enhancedMetadata.primary_content === 'string' 
          ? enhancedMetadata.primary_content 
          : JSON.stringify(enhancedMetadata.primary_content, null, 2);
        navigator.clipboard.writeText(textToCopy);
        break;
      
      case 'download_html':
        downloadFile(enhancedMetadata.primary_content, `${nodeName}_output.html`, 'text/html');
        break;
      
      case 'download_json':
        downloadFile(
          JSON.stringify(output, null, 2), 
          `${nodeName}_output.json`, 
          'application/json'
        );
        break;
      
      case 'download_images':
        enhancedMetadata.attachments.forEach(attachment => {
          if (attachment.type === 'image') {
            downloadFile(attachment.data, attachment.name, attachment.mime_type);
          }
        });
        break;
    }
  };
  
  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  if (!isExpanded) {
    return (
      <div className={cn("text-xs text-slate-400", className)}>
        {enhancedMetadata.display_type} • {enhancedMetadata.metadata.node_type}
      </div>
    );
  }
  
  return (
    <div className={cn("space-y-4", className)}>
      {/* Content Display based on type */}
      {renderContent(enhancedMetadata)}
      
      {/* Action Buttons */}
      {enhancedMetadata.actions.length > 0 && (
        <div className="flex items-center gap-2 pt-2 border-t border-white/10">
          {enhancedMetadata.actions.map(action => (
            <button
              key={action}
              onClick={() => handleAction(action)}
              className="text-xs px-2 py-1 rounded hover:bg-white/10 transition-colors text-slate-400 hover:text-white flex items-center gap-1"
              title={getActionTitle(action)}
            >
              {getActionIcon(action)}
              {getActionLabel(action)}
            </button>
          ))}
        </div>
      )}
      
      {/* Attachments */}
      {enhancedMetadata.attachments.length > 0 && (
        <div className="pt-2 border-t border-white/10">
          <div className="text-xs text-slate-400 mb-2">
            Attachments ({enhancedMetadata.attachments.length})
          </div>
          <div className="grid grid-cols-2 gap-2">
            {enhancedMetadata.attachments.map((attachment, idx) => (
              <div 
                key={idx}
                className="p-2 bg-white/5 rounded border border-white/10 text-xs"
              >
                <div className="font-medium text-slate-300">{attachment.name}</div>
                <div className="text-slate-500">{attachment.type}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Metadata Summary */}
      <details className="text-xs">
        <summary className="text-slate-400 cursor-pointer hover:text-slate-300">
          View Metadata
        </summary>
        <div className="mt-2 p-2 bg-white/5 rounded border border-white/10">
          <pre className="text-xs text-slate-400 overflow-auto max-h-32">
            {JSON.stringify(displayMetadata.metadata, null, 2)}
          </pre>
        </div>
      </details>
    </div>
  );
}

function renderContent(metadata: DisplayMetadata) {
  switch (metadata.display_type) {
    case 'text':
      return (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-purple-400 flex items-center gap-2">
            <FileText className="w-3.5 h-3.5" />
            Text Output
          </div>
          <div className="p-3 bg-black/40 rounded border border-white/10 text-sm text-slate-200 max-h-64 overflow-y-auto">
            <div className="whitespace-pre-wrap">{metadata.primary_content}</div>
          </div>
        </div>
      );
    
    case 'html':
      return (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-blue-400 flex items-center gap-2">
            <Code className="w-3.5 h-3.5" />
            Formatted Content
          </div>
          <div 
            className="p-3 bg-white/5 rounded border border-white/10 max-h-64 overflow-y-auto"
            dangerouslySetInnerHTML={{ __html: metadata.primary_content }}
          />
        </div>
      );
    
    case 'chart':
      return (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-green-400 flex items-center gap-2">
            <BarChart3 className="w-3.5 h-3.5" />
            Charts & Visualizations
          </div>
          <div className="space-y-3">
            {metadata.primary_content.charts?.map((chart: any, idx: number) => (
              <div key={idx} className="p-3 bg-white/5 rounded border border-white/10">
                <div className="text-sm font-medium text-slate-200 mb-2">
                  {chart.title || `Chart ${idx + 1}`}
                </div>
                {chart.image_base64 && (
                  <img 
                    src={chart.image_base64} 
                    alt={chart.title}
                    className="w-full h-auto rounded"
                    style={{ maxHeight: '300px', objectFit: 'contain' }}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      );
    
    case 'agent_report':
      return (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-cyan-400 flex items-center gap-2">
            <BarChart3 className="w-3.5 h-3.5" />
            Agent Report
          </div>
          {metadata.primary_content.summary && (
            <div className="p-3 bg-white/5 rounded border border-white/10 text-sm text-slate-200">
              {metadata.primary_content.summary}
            </div>
          )}
          {metadata.primary_content.agent_outputs && Object.keys(metadata.primary_content.agent_outputs).length > 0 && (
            <div className="space-y-2">
              <div className="text-xs text-slate-400">Individual Agent Outputs:</div>
              {Object.entries(metadata.primary_content.agent_outputs).map(([role, outputs]: [string, any]) => (
                <div key={role} className="p-2 bg-black/20 rounded border border-white/10">
                  <div className="text-xs font-medium text-cyan-400 mb-1">🤖 {role}</div>
                  {Array.isArray(outputs) && outputs.map((output: any, idx: number) => (
                    <div key={idx} className="text-xs text-slate-300 mb-1">
                      {output.output || output.result || 'No output available'}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    
    case 'data':
    default:
      return (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-amber-400 flex items-center gap-2">
            <Code className="w-3.5 h-3.5" />
            Raw Data
          </div>
          <div className="p-3 bg-black/40 rounded border border-white/10 text-xs max-h-64 overflow-y-auto">
            <pre className="text-slate-300">{JSON.stringify(metadata.primary_content, null, 2)}</pre>
          </div>
        </div>
      );
  }
}

function FallbackDisplay({ nodeType, output, className }: { nodeType: string; output: any; className?: string }) {
  return (
    <div className={cn("space-y-2", className)}>
      <div className="text-xs font-semibold text-red-400 flex items-center gap-2">
        <AlertCircle className="w-3.5 h-3.5" />
        Legacy Display ({nodeType})
      </div>
      <div className="p-3 bg-black/40 rounded border border-white/10 text-xs max-h-64 overflow-y-auto">
        <pre className="text-slate-300">{JSON.stringify(output, null, 2)}</pre>
      </div>
    </div>
  );
}

function getActionIcon(action: string) {
  switch (action) {
    case 'copy':
    case 'copy_markdown':
    case 'copy_individual':
      return <Copy className="w-3 h-3" />;
    case 'download_html':
    case 'download_json':
    case 'download_images':
    case 'download_report':
      return <Download className="w-3 h-3" />;
    default:
      return <FileText className="w-3 h-3" />;
  }
}

function getActionLabel(action: string) {
  switch (action) {
    case 'copy': return 'Copy';
    case 'copy_markdown': return 'Copy MD';
    case 'copy_individual': return 'Copy Parts';
    case 'download_html': return 'HTML';
    case 'download_json': return 'JSON';
    case 'download_images': return 'Images';
    case 'download_report': return 'Report';
    default: return action;
  }
}

function getActionTitle(action: string) {
  switch (action) {
    case 'copy': return 'Copy content to clipboard';
    case 'copy_markdown': return 'Copy as Markdown';
    case 'copy_individual': return 'Copy individual sections';
    case 'download_html': return 'Download as HTML file';
    case 'download_json': return 'Download as JSON file';
    case 'download_images': return 'Download all images';
    case 'download_report': return 'Download full report';
    default: return action;
  }
}