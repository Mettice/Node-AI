/**
 * Special field handlers for SchemaForm
 * Handles rendering of special field types (API keys, arrays, objects, etc.)
 */

import React from 'react';
import { APIKeyInput } from '../APIKeyInput';
import { APIKeyInputWithVault } from '../APIKeyInputWithVault';
import { ConnectionStringInput } from '../ConnectionStringInput';
import { FileSelector } from '../FileSelector';
import { KnowledgeBaseSelector } from '../KnowledgeBaseSelector';
import { ModelSelector } from '../ModelSelector';
import { ArrayInput } from '../ArrayInput';
import { ObjectInput } from '../ObjectInput';
import { MultiSelectDropdown } from '@/components/common/MultiSelectDropdown';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import { testSearchProviderConnection, testLLMConnection, testEmailConnection } from '@/services/nodes';

interface FieldHandlerContext {
  key: string;
  fieldSchema: any;
  formValues: Record<string, any>;
  setValue: (key: string, value: any) => void;
  required: string[];
  nodeType: string;
  isToolNode: boolean;
}

/**
 * Check if a field needs special handling and return the component
 */
export function getSpecialFieldHandler(context: FieldHandlerContext): React.ReactNode | null {
  const { key, fieldSchema, formValues, setValue, required, nodeType, isToolNode } = context;

  // Special handling for Gemini File Search toggle
  // Show for Chat nodes, but indicate it's Gemini-only
  if (key === 'gemini_use_file_search' && nodeType === 'chat') {
    const isGeminiProvider = formValues.provider === 'gemini' || formValues.provider === 'google';
    
    // If not Gemini provider, show disabled with explanation
    if (!isGeminiProvider) {
      return (
        <div key={key} className="space-y-2">
          <div className="p-3 bg-slate-500/10 border border-slate-500/30 rounded-lg opacity-60">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                disabled
                checked={false}
                className="w-4 h-4 text-blue-600 bg-white/5 border-white/20 rounded cursor-not-allowed"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-400">
                    {fieldSchema.title || 'Use File Search'}
                  </span>
                  <span className="px-2 py-0.5 text-xs font-semibold bg-blue-500/20 text-blue-300 rounded border border-blue-500/30">
                    GEMINI ONLY
                  </span>
                </div>
                {fieldSchema.description && (
                  <p className="text-xs text-slate-500 mt-1">
                    {fieldSchema.description}
                  </p>
                )}
                <p className="text-xs text-yellow-400 mt-2">
                  ⚠️ File Search is only available when using Gemini provider. Switch to Gemini to enable this feature.
                </p>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    // Show enabled toggle when Gemini is selected
    return (
      <div key={key} className="space-y-2">
        <label className="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-lg cursor-pointer hover:bg-blue-500/15 transition-colors">
          <input
            type="checkbox"
            checked={formValues[key] || false}
            onChange={(e) => setValue(key, e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-white/5 border-white/20 rounded focus:ring-blue-500 focus:ring-2"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-white">
                {fieldSchema.title || 'Use File Search'}
              </span>
            </div>
            {fieldSchema.description && (
              <p className="text-xs text-slate-400 mt-1">
                {fieldSchema.description}
              </p>
            )}
          </div>
        </label>
      </div>
    );
  }

  // Special handling for Gemini URL Context toggle
  // Show for Chat nodes, but indicate it's Gemini-only
  if (key === 'gemini_use_url_context' && nodeType === 'chat') {
    const isGeminiProvider = formValues.provider === 'gemini' || formValues.provider === 'google';
    
    // If not Gemini provider, show disabled with explanation
    if (!isGeminiProvider) {
      return (
        <div key={key} className="space-y-2">
          <div className="p-3 bg-slate-500/10 border border-slate-500/30 rounded-lg opacity-60">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                disabled
                checked={false}
                className="w-4 h-4 text-blue-600 bg-white/5 border-white/20 rounded cursor-not-allowed"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-400">
                    {fieldSchema.title || 'Enable URL Context'}
                  </span>
                  <span className="px-2 py-0.5 text-xs font-semibold bg-blue-500/20 text-blue-300 rounded border border-blue-500/30">
                    GEMINI ONLY
                  </span>
                </div>
                {fieldSchema.description && (
                  <p className="text-xs text-slate-500 mt-1">
                    {fieldSchema.description}
                  </p>
                )}
                <p className="text-xs text-yellow-400 mt-2">
                  ⚠️ URL Context is only available when using Gemini provider. Switch to Gemini to enable this feature.
                </p>
              </div>
            </div>
          </div>
        </div>
      );
    }
    return (
      <div key={key} className="space-y-2">
        <label className="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-lg cursor-pointer hover:bg-blue-500/15 transition-colors">
          <input
            type="checkbox"
            checked={formValues[key] || false}
            onChange={(e) => setValue(key, e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-white/5 border-white/20 rounded focus:ring-blue-500 focus:ring-2"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-white">
                {fieldSchema.title || 'Enable URL Context'}
              </span>
              <span className="px-2 py-0.5 text-xs font-semibold bg-blue-500/20 text-blue-300 rounded border border-blue-500/30">
                NEW
              </span>
            </div>
            {fieldSchema.description && (
              <p className="text-xs text-slate-400 mt-1">
                {fieldSchema.description}
              </p>
            )}
          </div>
        </label>
        {formValues[key] && (
          <div className="ml-7 p-2 bg-cyan-500/5 border border-cyan-500/20 rounded text-xs text-cyan-300">
            <p className="font-semibold mb-1">🌐 URL Context Active</p>
            <p className="text-cyan-400/80">
              Gemini will automatically fetch and analyze URLs from your prompt. You can include up to 20 URLs per request.
            </p>
          </div>
        )}
      </div>
    );
  }

  // Special handling for Agent Lightning toggle
  // Show for both CrewAI and LangChain agent nodes
  if (key === 'enable_agent_lightning') {
    const isAgentNode = nodeType === 'crewai_agent' || nodeType === 'langchain_agent';
    
    if (!isAgentNode) {
      return null; // Don't show for non-agent nodes
    }
    return (
      <div key={key} className="space-y-2">
        <label className="flex items-center gap-3 p-3 bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/30 rounded-lg cursor-pointer hover:bg-purple-500/15 transition-colors">
          <input
            type="checkbox"
            checked={formValues[key] || false}
            onChange={(e) => setValue(key, e.target.checked)}
            className="w-4 h-4 text-purple-600 bg-white/5 border-white/20 rounded focus:ring-purple-500 focus:ring-2"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-white">
                {fieldSchema.title || 'Enable Agent Lightning'}
              </span>
              <span className="px-2 py-0.5 text-xs font-semibold bg-purple-500/20 text-purple-300 rounded border border-purple-500/30">
                NEW
              </span>
            </div>
            {fieldSchema.description && (
              <p className="text-xs text-slate-400 mt-1">
                {fieldSchema.description}
              </p>
            )}
          </div>
        </label>
        {formValues[key] && (
          <div className="ml-7 p-2 bg-blue-500/5 border border-blue-500/20 rounded text-xs text-blue-300">
            <p className="font-semibold mb-1">⚡ Agent Lightning Active</p>
            <p className="text-blue-400/80">
              Your agent will automatically optimize using reinforcement learning and prompt optimization.
            </p>
          </div>
        )}
      </div>
    );
  }

  // Special handling for fine-tuned model selector
  if (key === 'finetuned_model_id' && formValues.use_finetuned_model) {
    const provider = formValues.provider || 'openai';
    return (
      <div key={key} className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          {fieldSchema.title || key}
          {required.includes(key) && <span className="text-red-400 ml-1">*</span>}
        </label>
        {fieldSchema.description && (
          <p className="text-xs text-slate-400 -mt-1">{fieldSchema.description}</p>
        )}
        <ModelSelector
          provider={provider}
          value={formValues[key] || ''}
          onChange={(modelId) => setValue(key, modelId)}
        />
      </div>
    );
  }

  // Special handling for file_loader and data_loader nodes
  if ((nodeType === 'file_loader' || nodeType === 'data_loader') && key === 'file_id') {
    return (
      <div key={key} className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          {fieldSchema.title || key}
          {required.includes(key) && <span className="text-red-400 ml-1">*</span>}
        </label>
        {fieldSchema.description && (
          <p className="text-xs text-slate-400 -mt-1">{fieldSchema.description}</p>
        )}
        <FileSelector
          value={formValues[key] || ''}
          onChange={(fileId) => setValue(key, fileId)}
          error={undefined}
        />
      </div>
    );
  }

  // Special handling for knowledge_base_id in vector_search nodes
  if (nodeType === 'vector_search' && key === 'knowledge_base_id') {
    return (
      <div key={key} className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          {fieldSchema.title || key}
          {required.includes(key) && <span className="text-red-400 ml-1">*</span>}
        </label>
        {fieldSchema.description && (
          <p className="text-xs text-slate-400 -mt-1">{fieldSchema.description}</p>
        )}
        <KnowledgeBaseSelector
          value={formValues[key] || ''}
          onChange={(kbId) => setValue(key, kbId)}
        />
      </div>
    );
  }

  // Special handling for S3 credentials (masked input)
  if (key === 's3_access_key_id' || key === 's3_secret_access_key') {
    return (
      <APIKeyInput
        key={key}
        value={formValues[key] || ''}
        onChange={(value) => setValue(key, value)}
        placeholder={fieldSchema.description || 'Enter AWS credential...'}
        label={fieldSchema.title || key}
        description={fieldSchema.description}
        required={required.includes(key)}
        serviceName={key === 's3_access_key_id' ? 'AWS Access Key ID' : 'AWS Secret Access Key'}
        testConnection={async () => {
          // S3 connection test would require bucket access, skip for now
          return true;
        }}
      />
    );
  }

  // Special handling for platform selection in Cost Optimizer
  if (nodeType === 'cost_optimizer' && key === 'platform') {
    const platformOptions = [
      { value: 'aws', label: 'AWS', icon: 'aws' },
      { value: 'gcp', label: 'Google Cloud Platform', icon: 'gcp' },
      { value: 'azure', label: 'Microsoft Azure', icon: 'microsoftazure' },
      { value: 'multi_cloud', label: 'Multi-Cloud', icon: 'cloud' },
    ];
    
    return (
      <div key={key} className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          {fieldSchema.title || key}
          {required.includes(key) && <span className="text-red-400 ml-1">*</span>}
        </label>
        {fieldSchema.description && (
          <p className="text-xs text-slate-400 -mt-1">{fieldSchema.description}</p>
        )}
        <SelectWithIcons
          value={formValues[key] || fieldSchema.default || 'aws'}
          onChange={(value) => setValue(key, value)}
          options={platformOptions}
          placeholder="Select cloud platform..."
        />
      </div>
    );
  }

  // Special handling for platforms in Social Analyzer
  if (nodeType === 'social_analyzer' && key === 'platforms') {
    // This will be handled by the enum array handler above, but we can add icons
    return null; // Let the enum array handler take care of it
  }

  // Special handling for analysis_types in Social Analyzer
  if (nodeType === 'social_analyzer' && key === 'analysis_types') {
    // This will be handled by the enum array handler above
    return null; // Let the enum array handler take care of it
  }

    // Special handling for API key fields (masked input with connect button)
  if (key.includes('api_key') || key.includes('_api_key')) {
    // For tool nodes with web_search, conditionally show API key fields based on provider
    if (isToolNode && formValues.tool_type === 'web_search') {
      const provider = formValues.web_search_provider || 'duckduckgo';
      
      if (key === 'serper_api_key' && provider !== 'serper') {
        return null;
      }
      if (key === 'perplexity_api_key' && provider !== 'perplexity') {
        return null;
      }
      if (key === 'web_search_api_key' && provider !== 'serpapi' && provider !== 'brave') {
        return null;
      }
    }
    
    // Determine service name and provider from field name
    let serviceName = 'API';
    let vaultProvider: string | undefined;
    
    if (key.includes('web_search')) {
      const provider = formValues.web_search_provider || 'duckduckgo';
      serviceName = provider === 'serpapi' ? 'SerpAPI' : provider === 'brave' ? 'Brave Search' : 'DuckDuckGo';
    } else if (key.includes('serper')) {
      serviceName = 'Serper';
    } else if (key.includes('perplexity')) {
      serviceName = 'Perplexity';
    } else if (key.includes('resend')) {
      serviceName = 'Resend';
    } else if (key.includes('azure_openai') || (key.includes('azure') && key.includes('openai'))) {
      serviceName = 'Azure OpenAI';
      vaultProvider = 'azure_openai';
    } else if (key.includes('openai')) {
      serviceName = 'OpenAI';
      vaultProvider = 'openai';
    } else if (key.includes('anthropic')) {
      serviceName = 'Anthropic';
      vaultProvider = 'anthropic';
    } else if (key.includes('gemini')) {
      serviceName = 'Google Gemini';
      vaultProvider = 'google';
    } else if (key.includes('cohere')) {
      serviceName = 'Cohere';
      vaultProvider = 'cohere';
    } else if (key.includes('voyage')) {
      serviceName = 'Voyage AI';
      vaultProvider = 'voyage_ai';
    } else if (key.includes('pinecone')) {
      serviceName = 'Pinecone';
      vaultProvider = 'pinecone';
    } else if (key.includes('azure_search') || (key.includes('azure') && key.includes('search'))) {
      serviceName = 'Azure Cognitive Search';
      vaultProvider = 'azure_cognitive_search';
    } else if (key.includes('reddit')) {
      serviceName = 'Reddit';
      vaultProvider = 'reddit';
    } else if (key.includes('web_search') || key.includes('serper') || key.includes('perplexity')) {
      // Web search providers - use generic provider or specific ones
      if (key.includes('serper')) {
        vaultProvider = 'serper';
      } else if (key.includes('perplexity')) {
        vaultProvider = 'perplexity';
      } else {
        vaultProvider = 'web_search';
      }
    } else if (key.includes('resend')) {
      vaultProvider = 'resend';
    }

    // Use vault-enabled component for all nodes that support API keys
    // This includes: LLM nodes, embedding nodes, agent nodes, processing nodes, retrieval nodes, storage nodes, tool nodes, integration nodes
    const nodesWithVaultSupport = [
      'chat', 'embed', 'rerank', 'vision', 'langchain_agent', 'crewai_agent',
      'advanced_nlp', 'transcribe', 'finetune',
      'search', 'vector_search',
      'vector_store',
      'tool', 'web_search',
      'reddit',
      // New LLM nodes using LLMConfigMixin
      'smart_data_analyzer', 'blog_generator', 'proposal_generator',
      'meeting_summarizer', 'lead_scorer', 'content_moderator', 'auto_chart_generator',
      'call_summarizer', 'followup_writer', 'lead_enricher',
      'stripe_analytics', 'cost_optimizer', 'social_analyzer', 'ab_test_analyzer',
      'brand_generator', 'podcast_transcriber', 'social_scheduler',
      'bug_triager', 'docs_writer', 'performance_monitor', 'security_scanner'
    ];
    // Check if node type matches (exact match or contains the node type)
    const isVaultSupportedNode = nodesWithVaultSupport.some(node => 
      nodeType === node || nodeType.includes(node) || node.includes(nodeType)
    ) || isToolNode; // Tool nodes always support vault
    
    // Get provider from formValues if not determined from key
    let actualProvider = vaultProvider || formValues.provider;
    // Map provider names to vault provider names
    if (actualProvider === 'gemini' || actualProvider === 'google') {
      actualProvider = 'google';
    }
    // For tool nodes, we might not have a provider in formValues, so use vaultProvider if available
    if (isToolNode && !actualProvider && vaultProvider) {
      actualProvider = vaultProvider;
    }
    const shouldUseVault = isVaultSupportedNode && actualProvider && (key.includes('api_key') || key === 'api_key');

    const testConnectionFn = async (apiKey: string) => {
      if (key.includes('web_search')) {
        const provider = formValues.web_search_provider || 'duckduckgo';
        return await testSearchProviderConnection(provider, apiKey);
      } else if (key.includes('serper')) {
        return await testSearchProviderConnection('serper', apiKey);
      } else if (key.includes('perplexity')) {
        return await testSearchProviderConnection('perplexity', apiKey);
      } else if (key.includes('resend')) {
        return await testEmailConnection('resend', apiKey);
      } else if (key.includes('azure_openai') || (key.includes('azure') && key.includes('openai'))) {
        // Azure OpenAI connection test - you may need to implement this
        return true;
      } else if (key.includes('openai')) {
        return await testLLMConnection('openai', apiKey);
      } else if (key.includes('anthropic')) {
        return await testLLMConnection('anthropic', apiKey);
      } else if (key.includes('gemini')) {
        return await testLLMConnection('gemini', apiKey);
      } else if (key.includes('cohere')) {
        return await testLLMConnection('cohere', apiKey);
      } else if (key.includes('voyage')) {
        return await testLLMConnection('voyage_ai', apiKey);
      }
      return true;
    };

    if (shouldUseVault) {
      // Check if there's a secret_id in config (for loading existing vault secrets)
      const secretIdKey = `${key}_secret_id`;
      const existingSecretId = formValues[secretIdKey];
      
      return (
        <APIKeyInputWithVault
          key={key}
          value={formValues[key] || ''}
          secretId={existingSecretId}
          onChange={(value, secretId) => {
            // Store the API key value
            setValue(key, value);
            // Store secret_id in config (for backend to use) but don't show it as a separate field
            if (secretId) {
              setValue(secretIdKey, secretId);
            } else {
              // Clear secret_id when not using vault
              setValue(secretIdKey, undefined);
            }
          }}
          placeholder={fieldSchema.description || 'Enter API key...'}
          label={fieldSchema.title || key}
          description={fieldSchema.description}
          required={required.includes(key)}
          serviceName={serviceName}
          provider={actualProvider}
          testConnection={testConnectionFn}
        />
      );
    }

    return (
      <APIKeyInput
        key={key}
        value={formValues[key] || ''}
        onChange={(value) => setValue(key, value)}
        placeholder={fieldSchema.description || 'Enter API key...'}
        label={fieldSchema.title || key}
        description={fieldSchema.description}
        required={required.includes(key)}
        serviceName={serviceName}
        testConnection={testConnectionFn}
      />
    );
  }

  // Special handling for database connection string
  if (key === 'database_connection_string' && isToolNode && formValues.tool_type === 'database_query') {
    const databaseType = formValues.database_type || 'sqlite';
    return (
      <ConnectionStringInput
        key={key}
        value={formValues[key] || ''}
        onChange={(value) => setValue(key, value)}
        databaseType={databaseType}
        label={fieldSchema.title || key}
        description={fieldSchema.description}
        required={required.includes(key)}
      />
    );
  }

  // Special handling for Gemini URL Context URLs array
  if (key === 'gemini_url_context_urls' && nodeType === 'chat' && formValues.gemini_use_url_context) {
    return (
      <div key={key} className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          {fieldSchema.title || 'URLs to Analyze'}
          {required.includes(key) && <span className="text-red-400 ml-1">*</span>}
        </label>
        {fieldSchema.description && (
          <p className="text-xs text-slate-400 -mt-1">{fieldSchema.description}</p>
        )}
        <div className="p-2 bg-blue-500/5 border border-blue-500/20 rounded text-xs text-blue-300 mb-2">
          <p className="font-semibold mb-1">💡 Tip</p>
          <p className="text-blue-400/80">
            You can also include URLs directly in your prompt text. Gemini will automatically fetch them when URL Context is enabled.
          </p>
        </div>
        <ArrayInput
          value={formValues[key] || []}
          onChange={(value) => setValue(key, value)}
          placeholder="https://example.com/page"
        />
        {formValues[key] && formValues[key].length > 0 && (
          <p className="text-xs text-slate-500">
            {formValues[key].length} URL(s) added (max 20 per request)
          </p>
        )}
      </div>
    );
  }

  // Special handling for array fields with strings
  if (fieldSchema.type === 'array' && fieldSchema.items?.type === 'string') {
    // If items have enum values, use multi-select dropdown instead of ArrayInput
    if (fieldSchema.items?.enum) {
      // Format options for MultiSelectDropdown
      const formatLabel = (val: string) => {
        return val
          .replace(/_/g, ' ')
          .replace(/\b\w/g, (l) => l.toUpperCase());
      };

      const dropdownOptions = fieldSchema.items.enum.map((val: string) => ({
        value: val,
        label: formatLabel(val),
        // Add icons for specific options if needed
        icon: val === 'aws' ? 'aws' : 
              val === 'gcp' ? 'gcp' : 
              val === 'azure' ? 'microsoftazure' :
              val === 'twitter' ? 'twitter' :
              val === 'linkedin' ? 'linkedin' :
              val === 'facebook' ? 'facebook' :
              val === 'instagram' ? 'instagram' :
              undefined
      }));

      return (
        <div key={key} className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            {fieldSchema.title || key}
            {required.includes(key) && <span className="text-red-400 ml-1">*</span>}
          </label>
          {fieldSchema.description && (
            <p className="text-xs text-slate-400 -mt-1">{fieldSchema.description}</p>
          )}
          <MultiSelectDropdown
            value={formValues[key] || []}
            onChange={(selected) => setValue(key, selected)}
            options={dropdownOptions}
            placeholder={fieldSchema.description || `Select ${fieldSchema.title?.toLowerCase() || 'options'}...`}
            maxSelections={fieldSchema.maxItems}
          />
        </div>
      );
    }
    
    // Regular array input for non-enum arrays
    return (
      <div key={key} className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          {fieldSchema.title || key}
          {required.includes(key) && <span className="text-red-400 ml-1">*</span>}
        </label>
        {fieldSchema.description && (
          <p className="text-xs text-slate-400 -mt-1">{fieldSchema.description}</p>
        )}
        <ArrayInput
          value={formValues[key] || []}
          onChange={(value) => setValue(key, value)}
          placeholder={fieldSchema.items?.description || 'Enter value'}
        />
      </div>
    );
  }

  // Special handling for object fields
  if (fieldSchema.type === 'object' && !fieldSchema.properties) {
    return (
      <div key={key} className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          {fieldSchema.title || key}
          {required.includes(key) && <span className="text-red-400 ml-1">*</span>}
        </label>
        {fieldSchema.description && (
          <p className="text-xs text-slate-400 -mt-1">{fieldSchema.description}</p>
        )}
        <ObjectInput
          value={formValues[key] || {}}
          onChange={(value) => setValue(key, value)}
        />
      </div>
    );
  }

  return null;
}

