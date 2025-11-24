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
      'reddit'
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
      return (
        <APIKeyInputWithVault
          key={key}
          value={formValues[key] || ''}
          secretId={formValues[`${key}_secret_id`]}
          onChange={(value, secretId) => {
            setValue(key, value);
            // Store secret ID if using vault, clear it if not
            if (secretId) {
              setValue(`${key}_secret_id`, secretId);
            } else {
              // Explicitly remove the secret_id field when clearing
              const currentValues = formValues;
              if (currentValues[`${key}_secret_id`]) {
                setValue(`${key}_secret_id`, undefined);
              }
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

  // Special handling for array fields with strings
  if (fieldSchema.type === 'array' && fieldSchema.items?.type === 'string') {
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

