/**
 * Node configuration display component
 * Shows config preview based on node type
 */

import { ProviderIcon } from '@/components/common/ProviderIcon';

interface NodeConfigDisplayProps {
  type: string;
  config: Record<string, any>;
}

export function NodeConfigDisplay({ type, config }: NodeConfigDisplayProps) {
  if (!config || Object.keys(config).length === 0) {
    return (
      <div className="text-slate-400 italic text-center py-0.5 px-1 text-[9px]">
        Click to configure
      </div>
    );
  }

  // Chunk node - single line with ellipsis truncation
  if (type === 'chunk') {
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        {config.strategy && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Strategy:</span>
            <span className="text-slate-100 font-medium capitalize truncate text-right drop-shadow-sm max-w-[120px]" title={config.strategy}>
              {config.strategy}
            </span>
          </div>
        )}
        {config.chunk_size && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Size:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={String(config.chunk_size)}>
              {config.chunk_size}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Embed node - single line with ellipsis truncation
  if (type === 'embed') {
    const model = config.openai_model || config.hf_model || config.cohere_model || config.gemini_model || config.voyage_model;
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        {config.provider && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Provider:</span>
            <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
              <ProviderIcon provider={config.provider} size="sm" className="flex-shrink-0" />
              <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={config.provider}>
                {config.provider}
              </span>
            </div>
          </div>
        )}
        {model && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Model:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={model}>
              {model}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Chat node - single line with ellipsis truncation
  if (type === 'chat') {
    const model = config.openai_model || config.anthropic_model || config.gemini_model;
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        {config.provider && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Provider:</span>
            <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
              <ProviderIcon provider={config.provider} size="sm" className="flex-shrink-0" />
              <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={config.provider}>
                {config.provider}
              </span>
            </div>
          </div>
        )}
        {model && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Model:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={model}>
              {model}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Vision node - single line with ellipsis truncation
  if (type === 'vision') {
    const model = config.openai_model || config.anthropic_model || config.gemini_model;
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        {config.provider && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Provider:</span>
            <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
              <ProviderIcon provider={config.provider} size="sm" className="flex-shrink-0" />
              <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={config.provider}>
                {config.provider}
              </span>
            </div>
          </div>
        )}
        {model && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Model:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={model}>
              {model}
            </span>
          </div>
        )}
      </div>
    );
  }

  // S3 Storage node - single line with ellipsis truncation
  if (type === 's3') {
    const operation = config.s3_operation || 'list';
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        <div className="flex justify-between items-center text-[10px] gap-2">
          <span className="text-slate-400 flex-shrink-0">Operation:</span>
          <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
            <ProviderIcon provider="s3" size="sm" className="flex-shrink-0" />
            <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={operation}>
              {operation}
            </span>
          </div>
        </div>
        {config.s3_bucket && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Bucket:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={config.s3_bucket}>
              {config.s3_bucket}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Email node - single line with ellipsis truncation
  if (type === 'email') {
    const toEmail = config.email_to || 'Not set';
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        <div className="flex justify-between items-center text-[10px] gap-2">
          <span className="text-slate-400 flex-shrink-0">To:</span>
          <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
            <ProviderIcon provider="resend" size="sm" className="flex-shrink-0" />
            <span className="text-slate-100 truncate drop-shadow-sm max-w-[100px]" title={toEmail}>
              {toEmail}
            </span>
          </div>
        </div>
        {config.email_subject && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Subject:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={config.email_subject}>
              {config.email_subject}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Database node - single line with ellipsis truncation
  if (type === 'database') {
    const dbType = config.database_type || 'sqlite';
    const queryType = config.query_type || 'SELECT';
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        <div className="flex justify-between items-center text-[10px] gap-2">
          <span className="text-slate-400 flex-shrink-0">Type:</span>
          <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
            <ProviderIcon provider={dbType} size="sm" className="flex-shrink-0" />
            <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={dbType}>
              {dbType}
            </span>
          </div>
        </div>
        <div className="flex justify-between items-center text-[10px] gap-2">
          <span className="text-slate-400 flex-shrink-0">Query:</span>
          <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={queryType}>
            {queryType}
          </span>
        </div>
      </div>
    );
  }

  // Slack node - single line with ellipsis truncation
  if (type === 'slack') {
    const operation = config.slack_operation || 'send_message';
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        <div className="flex justify-between items-center text-[10px] gap-2">
          <span className="text-slate-400 flex-shrink-0">Operation:</span>
          <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
            <ProviderIcon provider="slack" size="sm" className="flex-shrink-0" />
            <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={operation.replace('_', ' ')}>
              {operation.replace('_', ' ')}
            </span>
          </div>
        </div>
        {config.slack_channel && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Channel:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={config.slack_channel}>
              {config.slack_channel}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Google Drive node - single line with ellipsis truncation
  if (type === 'google_drive') {
    const operation = config.google_drive_operation || 'list';
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        <div className="flex justify-between items-center text-[10px] gap-2">
          <span className="text-slate-400 flex-shrink-0">Operation:</span>
          <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
            <ProviderIcon provider="googledrive" size="sm" className="flex-shrink-0" />
            <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={operation.replace('_', ' ')}>
              {operation.replace('_', ' ')}
            </span>
          </div>
        </div>
        {config.google_drive_file_id && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">File ID:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={config.google_drive_file_id}>
              {config.google_drive_file_id.substring(0, 15)}...
            </span>
          </div>
        )}
      </div>
    );
  }

  // Reddit node - single line with ellipsis truncation
  if (type === 'reddit') {
    const operation = config.reddit_operation || 'fetch_posts';
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        <div className="flex justify-between items-center text-[10px] gap-2">
          <span className="text-slate-400 flex-shrink-0">Operation:</span>
          <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
            <ProviderIcon provider="reddit" size="sm" className="flex-shrink-0" />
            <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={operation.replace('_', ' ')}>
              {operation.replace('_', ' ')}
            </span>
          </div>
        </div>
        {config.reddit_subreddit && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Subreddit:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={config.reddit_subreddit}>
              r/{config.reddit_subreddit}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Vector Store node - single line with ellipsis truncation
  if (type === 'vector_store') {
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        {config.provider && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Provider:</span>
            <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
              <ProviderIcon provider={config.provider} size="sm" className="flex-shrink-0" />
              <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={config.provider}>
                {config.provider}
              </span>
            </div>
          </div>
        )}
        {config.faiss_index_type && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Type:</span>
            <span className="text-slate-200 capitalize truncate text-right max-w-[120px]" title={config.faiss_index_type}>
              {config.faiss_index_type}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Vector Search node - single line with ellipsis truncation
  if (type === 'knowledge_graph') {
    const operation = config.operation || 'query';
    return (
      <div className="space-y-1 text-xs">
        <div className="text-slate-300 font-medium">Operation: {operation.replace(/_/g, ' ')}</div>
        {operation === 'query' && config.cypher_query && (
          <div className="text-slate-400 truncate" title={config.cypher_query}>
            Query: {config.cypher_query.substring(0, 50)}...
          </div>
        )}
        {operation === 'create_node' && config.node_labels && (
          <div className="text-slate-400">
            Labels: {Array.isArray(config.node_labels) ? config.node_labels.join(', ') : config.node_labels}
          </div>
        )}
        {operation === 'create_relationship' && config.relationship_type && (
          <div className="text-slate-400">Type: {config.relationship_type}</div>
        )}
      </div>
    );
  }

  if (type === 'hybrid_retrieval') {
    const fusionMethod = config.fusion_method || 'reciprocal_rank';
    const vectorWeight = config.vector_weight || 0.7;
    const graphWeight = config.graph_weight || 0.3;
    return (
      <div className="space-y-1 text-xs">
        <div className="text-slate-300 font-medium">Fusion: {fusionMethod.replace(/_/g, ' ')}</div>
        {fusionMethod === 'weighted' && (
          <div className="text-slate-400">
            Weights: Vector {Math.round(vectorWeight * 100)}% / Graph {Math.round(graphWeight * 100)}%
          </div>
        )}
        {config.top_k && (
          <div className="text-slate-400">Top K: {config.top_k}</div>
        )}
      </div>
    );
  }

  if (type === 'vector_search') {
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        {config.top_k !== undefined && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Top K:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={String(config.top_k)}>
              {config.top_k}
            </span>
          </div>
        )}
        {config.score_threshold !== undefined && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Threshold:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={String(config.score_threshold)}>
              {config.score_threshold}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Memory node - single line with ellipsis truncation
  if (type === 'memory') {
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        {config.operation && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Operation:</span>
            <span className="text-slate-200 capitalize truncate text-right max-w-[120px]" title={config.operation}>
              {config.operation}
            </span>
          </div>
        )}
        {config.session_id && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Session:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={config.session_id}>
              {config.session_id}
            </span>
          </div>
        )}
      </div>
    );
  }

  // LangChain Agent node - single line with ellipsis truncation
  if (type === 'langchain_agent') {
    const model = config.openai_model || config.anthropic_model || config.gemini_model;
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        {config.provider && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Provider:</span>
            <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
              <ProviderIcon provider={config.provider} size="sm" className="flex-shrink-0" />
              <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={config.provider}>
                {config.provider}
              </span>
            </div>
          </div>
        )}
        {model && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Model:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={model}>
              {model}
            </span>
          </div>
        )}
      </div>
    );
  }

  // CrewAI Agent node - single line with ellipsis truncation
  if (type === 'crewai_agent') {
    const model = config.openai_model || config.anthropic_model || config.gemini_model;
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        {config.provider && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Provider:</span>
            <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
              <ProviderIcon provider={config.provider} size="sm" className="flex-shrink-0" />
              <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={config.provider}>
                {config.provider}
              </span>
            </div>
          </div>
        )}
        {model && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Model:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={model}>
              {model}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Tool node - show tool type with icon
  if (type === 'tool') {
    const toolType = config.tool_type;
    const toolName = config.tool_name;
    const displayName = toolName && toolName !== toolType 
      ? toolName 
      : toolType 
        ? toolType.split('_').map((word: string) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
        : null;
    
    return (
      <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
        {toolType && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Tool:</span>
            <div className="flex items-center gap-1.5 text-right min-w-0 flex-1 justify-end">
              <ProviderIcon provider={toolType} size="sm" className="flex-shrink-0" />
              <span className="text-slate-100 capitalize truncate drop-shadow-sm max-w-[100px]" title={displayName || toolType}>
                {displayName || toolType}
              </span>
            </div>
          </div>
        )}
        {/* Show additional config if available */}
        {config.web_search_provider && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Provider:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={config.web_search_provider}>
              {config.web_search_provider}
            </span>
          </div>
        )}
        {config.database_type && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Database:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={config.database_type}>
              {config.database_type}
            </span>
          </div>
        )}
        {config.s3_action && (
          <div className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 flex-shrink-0">Action:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={config.s3_action}>
              {config.s3_action}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Webhook Input node - show webhook URL
  if (type === 'webhook_input') {
    const webhookUrl = config.webhook_url;
    if (webhookUrl) {
      // Extract just the path for display
      try {
        const url = new URL(webhookUrl);
        const displayUrl = url.pathname;
        return (
          <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
            <div className="flex items-center gap-1.5 text-[10px]">
              <span className="text-slate-400 flex-shrink-0">URL:</span>
              <span className="text-slate-100 truncate font-mono drop-shadow-sm max-w-[140px]" title={webhookUrl}>
                {displayUrl}
              </span>
            </div>
            {config.name && (
              <div className="flex items-center gap-1.5 text-[10px]">
                <span className="text-slate-400 flex-shrink-0">Name:</span>
                <span className="text-slate-100 truncate drop-shadow-sm max-w-[140px]" title={config.name}>
                  {config.name}
                </span>
              </div>
            )}
          </div>
        );
      } catch {
        // Invalid URL, show as-is
        return (
          <div className="text-slate-100 text-[10px] truncate px-1 max-w-[160px]" title={webhookUrl}>
            {webhookUrl}
          </div>
        );
      }
    }
    return (
      <div className="text-slate-400 italic text-center py-0.5 px-1 text-[9px]">
        Webhook will be created
      </div>
    );
  }

  // Fallback: Show first 2 config fields vertically with ellipsis truncation
  const entries = Object.entries(config).slice(0, 2);
  
  return (
    <div className="space-y-0.5 px-1 max-h-[48px] overflow-hidden">
      {entries.map(([key, value]) => {
        const displayValue = String(value);
        return (
          <div key={key} className="flex justify-between items-center text-[10px] gap-2">
            <span className="text-slate-400 capitalize flex-shrink-0">{key.replace(/_/g, ' ')}:</span>
            <span className="text-slate-100 truncate text-right drop-shadow-sm max-w-[120px]" title={displayValue}>
              {displayValue}
            </span>
          </div>
        );
      })}
    </div>
  );
}

