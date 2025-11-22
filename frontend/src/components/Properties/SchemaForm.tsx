/**
 * Dynamic form generator from JSON schema
 */

import { useForm } from 'react-hook-form';
import { useEffect, useRef } from 'react';
import { ProviderSelector } from './ProviderSelector';
import { ToolTypeSelector } from './ToolTypeSelector';
import { CrewAIAgentForm } from './CrewAIAgentForm';
import { S3NodeForm } from './S3NodeForm';
import { EmailNodeForm } from './EmailNodeForm';
import { DatabaseNodeForm } from './DatabaseNodeForm';
import { SlackNodeForm } from './SlackNodeForm';
import { GoogleDriveNodeForm } from './GoogleDriveNodeForm';
import { RedditNodeForm } from './RedditNodeForm';
import { WebhookInputNodeForm } from './WebhookInputNodeForm';
import { AdvancedNLPForm } from './AdvancedNLPForm';
import { ProviderIcon } from '@/components/common/ProviderIcon';
import { shouldShowField } from './SchemaForm/FieldFilters';
import { renderField } from './SchemaForm/FieldRenderers';

interface SchemaFormProps {
  schema?: Record<string, any>;
  nodeType: string;
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
}

// Generic nodes that need provider selection
const GENERIC_NODES = ['embed', 'vector_store', 'vector_search', 'chat', 'vision', 'langchain_agent', 'crewai_agent'];
// Tool node needs tool_type selection
const TOOL_NODE = 'tool';
// Rerank node needs method selection
const RERANK_NODE = 'rerank';
// Knowledge Graph node needs operation selection
const KNOWLEDGE_GRAPH_NODE = 'knowledge_graph';
// Hybrid Retrieval node (special handling)
const HYBRID_RETRIEVAL_NODE = 'hybrid_retrieval';

export function SchemaForm({
  schema,
  nodeType,
  initialData,
  onChange,
}: SchemaFormProps) {
  const isGenericNode = GENERIC_NODES.includes(nodeType);
  const isToolNode = nodeType === TOOL_NODE;
  const isRerankNode = nodeType === RERANK_NODE;
  const isKnowledgeGraphNode = nodeType === KNOWLEDGE_GRAPH_NODE;
  const isHybridRetrievalNode = nodeType === HYBRID_RETRIEVAL_NODE;
  const isCrewAINode = nodeType === 'crewai_agent';
  const isS3Node = nodeType === 's3';
  const isEmailNode = nodeType === 'email';
  const isDatabaseNode = nodeType === 'database';
  const isSlackNode = nodeType === 'slack';
  const isGoogleDriveNode = nodeType === 'google_drive';
  const isRedditNode = nodeType === 'reddit';
  const isWebhookInputNode = nodeType === 'webhook_input';
  const isAdvancedNLPNode = nodeType === 'advanced_nlp';
  
  // Merge schema defaults with initial data (schema defaults take precedence if initialData is empty)
  const getDefaultValues = () => {
    const properties = schema?.properties || {};
    const defaults: Record<string, any> = {};
    
    // Get defaults from schema with proper type conversion
    Object.entries(properties).forEach(([key, fieldSchema]: [string, any]) => {
      if (fieldSchema.default !== undefined) {
        defaults[key] = fieldSchema.default;
      }
    });
    
    // Override with actual initial data (if provided), converting string numbers to actual numbers
    const typedInitialData: Record<string, any> = {};
    Object.entries(initialData).forEach(([key, value]) => {
      const fieldSchema = properties[key];
      if (fieldSchema) {
        const fieldType = fieldSchema.type;
        // Convert string numbers to actual numbers
        if ((fieldType === 'number' || fieldType === 'integer') && typeof value === 'string') {
          const numValue = fieldType === 'integer' ? parseInt(value, 10) : parseFloat(value);
          typedInitialData[key] = isNaN(numValue) ? value : numValue;
        } else {
          typedInitialData[key] = value;
        }
      } else {
        typedInitialData[key] = value;
      }
    });
    
    return { ...defaults, ...typedInitialData };
  };
  
  const { control, watch, setValue } = useForm({
    defaultValues: getDefaultValues(),
  });

  // Watch all form values
  const formValues = watch();
  const prevValuesRef = useRef<string>('');
  const onChangeRef = useRef(onChange);
  
  // Watch provider specifically to ensure re-render when it changes
  const currentProvider = watch('provider');

  // Update ref when onChange changes
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  // Update parent on form change (debounced and only when values actually change)
  useEffect(() => {
    const currentValuesStr = JSON.stringify(formValues);
    
    // Only call onChange if values actually changed
    if (currentValuesStr !== prevValuesRef.current) {
      prevValuesRef.current = currentValuesStr;
      
      // Debounce the onChange call
      const timeoutId = setTimeout(() => {
        // Clean up the values - remove undefined and empty strings
        const cleanedValues = Object.entries(formValues).reduce((acc, [key, value]) => {
          if (value !== undefined && value !== '' && value !== null) {
            acc[key] = value;
          }
          return acc;
        }, {} as Record<string, any>);
        
        // CRITICAL: For generic nodes, ensure provider is always included
        if (isGenericNode && formValues.provider) {
          cleanedValues.provider = formValues.provider;
        }
        
        // CRITICAL: For tool nodes, ensure tool_type is always included
        if (isToolNode && formValues.tool_type) {
          cleanedValues.tool_type = formValues.tool_type;
        }
        
        onChangeRef.current(cleanedValues);
      }, 300);

      return () => clearTimeout(timeoutId);
    }
  }, [formValues, nodeType, isGenericNode, isToolNode]);

  // Handle provider change
  const handleProviderChange = (provider: string) => {
    setValue('provider', provider);
    // Clear all provider-specific fields when provider changes
    const providerPrefixes = {
      openai: ['openai_'],
      huggingface: ['hf_', 'huggingface_'],
      cohere: ['cohere_'],
      anthropic: ['anthropic_'],
      voyage_ai: ['voyage_'],
      gemini: ['gemini_'],
      faiss: ['faiss_'],
      pinecone: ['pinecone_'],
    };
    
    // Clear fields that belong to other providers
    Object.keys(formValues).forEach((key) => {
      const belongsToOtherProvider = Object.entries(providerPrefixes).some(([prov, prefixes]) => {
        if (prov === provider) return false; // Don't clear current provider's fields
        return prefixes.some(prefix => key.startsWith(prefix));
      });
      
      if (belongsToOtherProvider) {
        setValue(key, undefined);
      }
    });
    
    // Set default values for the new provider's fields from schema
    const properties = schema?.properties || {};
    Object.keys(properties).forEach((key) => {
      const fieldSchema = properties[key];
      const currentPrefixes = providerPrefixes[provider as keyof typeof providerPrefixes] || [];
      const isCurrentProviderField = currentPrefixes.some(prefix => key.startsWith(prefix));
      
      if (isCurrentProviderField && fieldSchema.default !== undefined) {
        setValue(key, fieldSchema.default);
      }
    });
  };

  // Handle tool_type change
  const handleToolTypeChange = (toolType: string) => {
    setValue('tool_type', toolType);
    
    // Update tool_name and tool_description defaults based on tool type
    const toolDefaults: Record<string, { name: string; description: string }> = {
      calculator: { name: 'calculator', description: 'Calculator tool for mathematical expressions' },
      web_search: { name: 'web_search', description: 'Web search tool for finding information online' },
      web_scraping: { name: 'web_scraping', description: 'Web scraping tool for extracting content from web pages' },
      rss_feed: { name: 'rss_feed', description: 'RSS feed reader for aggregating content from feeds' },
      s3_storage: { name: 's3_storage', description: 'S3 storage tool for managing files in AWS S3 buckets' },
      code_execution: { name: 'code_execution', description: 'Code execution tool for running Python or JavaScript code' },
      database_query: { name: 'database_query', description: 'Database query tool for executing SQL queries' },
      api_call: { name: 'api_call', description: 'API call tool for making HTTP requests' },
      email: { name: 'email', description: 'Email tool for sending emails via Resend' },
      custom: { name: 'custom_tool', description: 'Custom tool for custom functionality' },
    };
    
    const defaults = toolDefaults[toolType];
    if (defaults) {
      // Only set defaults if fields are empty
      if (!formValues.tool_name || formValues.tool_name === formValues.tool_type) {
        setValue('tool_name', defaults.name);
      }
      if (!formValues.tool_description || formValues.tool_description.includes('Calculator tool')) {
        setValue('tool_description', defaults.description);
      }
    }
    
    // Clear tool_type-specific fields when tool type changes
    const toolTypePrefixes = ['calculator_', 'web_search_', 'web_scraping_', 'rss_feed_', 's3_', 'code_execution_', 'database_', 'api_call_', 'email_', 'resend_'];
    Object.keys(formValues).forEach((key) => {
      // Clear fields that belong to other tool types
      const belongsToOtherType = toolTypePrefixes.some(prefix => {
        if (key.startsWith(prefix)) {
          const expectedPrefix = `${toolType}_`;
          return !key.startsWith(expectedPrefix);
        }
        return false;
      });
      if (belongsToOtherType) {
        setValue(key, undefined);
      }
    });
  };

  // Check for custom forms FIRST (before schema validation)
  // These forms can work without a schema or handle their own schema
  
  // Use custom form for Webhook Input node (works without schema)
  if (isWebhookInputNode) {
    return <WebhookInputNodeForm initialData={initialData} onChange={onChange} />;
  }

  if (isAdvancedNLPNode) {
    return <AdvancedNLPForm initialData={initialData} onChange={onChange} />;
  }

  // Use custom form for CrewAI agent
  if (isCrewAINode) {
    return <CrewAIAgentForm initialData={initialData} onChange={onChange} schema={schema || {}} />;
  }

  // Use custom form for S3 node
  if (isS3Node) {
    return <S3NodeForm initialData={initialData} onChange={onChange} schema={schema || {}} />;
  }

  // Use custom form for Email node
  if (isEmailNode) {
    return <EmailNodeForm initialData={initialData} onChange={onChange} schema={schema || {}} />;
  }

  // Use custom form for Database node
  if (isDatabaseNode) {
    return <DatabaseNodeForm initialData={initialData} onChange={onChange} schema={schema || {}} />;
  }

  // Use custom form for Slack node
  if (isSlackNode) {
    return <SlackNodeForm initialData={initialData} onChange={onChange} schema={schema || {}} />;
  }

  // Use custom form for Google Drive node
  if (isGoogleDriveNode) {
    return <GoogleDriveNodeForm initialData={initialData} onChange={onChange} schema={schema || {}} />;
  }

  // Use custom form for Reddit node
  if (isRedditNode) {
    return <RedditNodeForm initialData={initialData} onChange={onChange} schema={schema || {}} />;
  }

  // Now validate schema for other nodes
  if (!schema || typeof schema !== 'object') {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No configuration schema available</p>
      </div>
    );
  }

  // Get properties for field ordering
  const properties = schema.properties || {};
  const required = schema.required || [];

  return (
    <div className="space-y-4">
      {/* Provider selector for generic nodes - show first */}
      {isGenericNode && (
        <ProviderSelector
          nodeType={nodeType}
          currentProvider={formValues.provider || ''}
          onChange={handleProviderChange}
        />
      )}

      {/* Tool type selector for tool nodes */}
      {isToolNode && (
        <div className="space-y-3">
          {/* Tool icon display */}
          {formValues.tool_type && (
            <div className="flex items-center gap-3 px-3 py-2 bg-white/5 border border-white/10 rounded-lg">
              <ProviderIcon 
                provider={formValues.tool_type} 
                size="md" 
                className="flex-shrink-0"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {formValues.tool_type
                    .split('_')
                    .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ')}
                </p>
                {formValues.tool_name && formValues.tool_name !== formValues.tool_type && (
                  <p className="text-xs text-slate-400 truncate">
                    {formValues.tool_name}
                  </p>
                )}
              </div>
            </div>
          )}
          <ToolTypeSelector
            currentToolType={formValues.tool_type || ''}
            onChange={handleToolTypeChange}
          />
        </div>
      )}

      {/* Method selector for rerank nodes */}
      {isRerankNode && (
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Reranking Method <span className="text-red-400">*</span>
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            Select the reranking method to use
          </p>
          <select
            value={formValues.method || 'cohere'}
            onChange={(e) => {
              setValue('method', e.target.value);
              // Clear method-specific fields when method changes
              const methodFields = ['model', 'voyage_model', 'llm_model'];
              methodFields.forEach((field) => {
                setValue(field, undefined);
              });
            }}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          >
            <option value="cohere">Cohere</option>
            <option value="voyage_ai">Voyage AI</option>
            <option value="cross_encoder">Cross-Encoder (Local)</option>
            <option value="llm">LLM-based</option>
          </select>
        </div>
      )}

      {/* Form fields */}
      {Object.entries(properties).map(([key, fieldSchema]: [string, any]) => {
        // Use field filter to determine if field should be shown
                const shouldShow = shouldShowField(key, {
                  nodeType,
                  formValues,
                  properties,
                  isGenericNode,
                  isToolNode,
                  isRerankNode,
                  isKnowledgeGraphNode,
                  isHybridRetrievalNode,
                  currentProvider,
                });

        if (!shouldShow) {
          return null;
        }

        // Special handling for knowledge_base_id (needs to clear index_id)
        if (nodeType === 'vector_search' && key === 'knowledge_base_id') {
          return renderField({
            key,
            fieldSchema,
            formValues,
            setValue: (k: string, v: any) => {
              setValue(k, v);
              if (k === 'knowledge_base_id' && v) {
                setValue('index_id', '');
              }
            },
            required,
            nodeType,
            isToolNode,
            control,
          });
        }

        // Render field using modular renderer
        return renderField({
          key,
          fieldSchema,
          formValues,
          setValue,
          required,
          nodeType,
          isToolNode,
          control,
        });
      })}
    </div>
  );
}

