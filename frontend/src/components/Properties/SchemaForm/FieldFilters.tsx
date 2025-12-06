/**
 * Field filtering logic for SchemaForm
 * Handles showing/hiding fields based on node type, provider, tool type, etc.
 */

export interface FieldFilterContext {
  nodeType: string;
  formValues: Record<string, any>;
  properties: Record<string, any>;
  isGenericNode: boolean;
  isToolNode: boolean;
  isRerankNode: boolean;
  isKnowledgeGraphNode?: boolean;
  isHybridRetrievalNode?: boolean;
  currentProvider?: string;
}

/**
 * Check if a field should be shown based on node type and configuration
 */
export function shouldShowField(
  key: string,
  context: FieldFilterContext
): boolean {
  const { nodeType, formValues, properties, isGenericNode, isToolNode, isRerankNode, isKnowledgeGraphNode, isHybridRetrievalNode, currentProvider } = context;

  // Skip provider field if it's a generic node (handled by ProviderSelector)
  if (isGenericNode && key === 'provider') {
    return false;
  }

  // Skip tool_type field if it's a tool node (handled by ToolTypeSelector)
  if (isToolNode && key === 'tool_type') {
    return false;
  }

  // Skip method field if it's a rerank node (handled by MethodSelector)
  if (isRerankNode && key === 'method') {
    return false;
  }

  // For generic nodes, hide the generic "model" field if provider-specific model fields exist
  if (isGenericNode && key === 'model') {
    const hasProviderSpecificModel = 
      (formValues.provider === 'openai' && properties['openai_model']) ||
      (formValues.provider === 'anthropic' && properties['anthropic_model']) ||
      ((formValues.provider === 'gemini' || formValues.provider === 'google') && properties['gemini_model']);
    
    if (hasProviderSpecificModel) {
      return false;
    }
  }

  // For rerank nodes, filter method-specific model fields
  if (isRerankNode && formValues.method) {
    const currentMethod = formValues.method;
    
    if (key === 'model' && currentMethod !== 'cohere') {
      return false;
    }
    if (key === 'voyage_model' && currentMethod !== 'voyage_ai') {
      return false;
    }
    if (key === 'llm_model' && currentMethod !== 'llm') {
      return false;
    }
  }

  // For tool nodes, filter tool_type-specific fields
  if (isToolNode && formValues.tool_type) {
    const currentToolType = formValues.tool_type;
    const toolTypePrefixes: Record<string, string[]> = {
      calculator: ['calculator_'],
      web_search: ['web_search_', 'serper_', 'perplexity_'],
      web_scraping: ['web_scraping_'],
      rss_feed: ['rss_feed_'],
      s3_storage: ['s3_'],
      code_execution: ['code_execution_'],
      database_query: ['database_'],
      api_call: ['api_call_'],
      email: ['email_', 'resend_'],
    };
    
    const currentPrefixes = toolTypePrefixes[currentToolType] || [];
    const belongsToOtherType = Object.entries(toolTypePrefixes).some(([toolType, prefixes]) => {
      if (toolType === currentToolType) return false;
      return prefixes.some(prefix => key.startsWith(prefix));
    });
    
    if (belongsToOtherType) {
      return false;
    }
    
    const isCommonField = !Object.values(toolTypePrefixes).flat().some(prefix => key.startsWith(prefix));
    const isCurrentToolTypeField = currentPrefixes.some(prefix => key.startsWith(prefix));
    
    if (!isCommonField && !isCurrentToolTypeField) {
      return false;
    }
  }

  // Hide index_id if knowledge_base_id is set (for vector_search)
  if (nodeType === 'vector_search' && key === 'index_id' && formValues.knowledge_base_id) {
    return false;
  }

  // Special fields that should always be shown (handled by special handlers)
  // Check this FIRST before any provider filtering
  const specialFields = [
    'gemini_use_url_context',
    'gemini_url_context_urls',
    'gemini_use_file_search',
    'enable_agent_lightning',
  ];
  
  // Always show special fields - they have their own visibility logic in FieldHandlers
  if (specialFields.includes(key)) {
    return true;
  }

  // For generic nodes, filter provider-specific fields
  if (isGenericNode && (formValues.provider || currentProvider)) {
    const currentProviderValue = formValues.provider || currentProvider;
    const providerPrefixes: Record<string, string[]> = {
      openai: ['openai_'],
      azure_openai: ['azure_openai_', 'azure_'],
      huggingface: ['hf_', 'huggingface_'],
      cohere: ['cohere_'],
      anthropic: ['anthropic_'],
      voyage_ai: ['voyage_'],
      gemini: ['gemini_'],
      faiss: ['faiss_'],
      pinecone: ['pinecone_'],
      gemini_file_search: ['gemini_'],
    };
    
    const normalizedProvider = currentProviderValue === 'google' ? 'gemini' : currentProviderValue;
    const currentPrefixes = providerPrefixes[normalizedProvider as keyof typeof providerPrefixes] || 
                            providerPrefixes[currentProviderValue as keyof typeof providerPrefixes] || [];
    
    // Special handling for Vector Store: when gemini_file_search is selected, show gemini_ fields
    if (nodeType === 'vector_store' && currentProviderValue === 'gemini_file_search') {
      if (key.startsWith('gemini_')) {
        // Show gemini_ fields for File Search
      } else if (key.startsWith('faiss_') || key.startsWith('pinecone_')) {
        return false;
      }
    }
    
    // Special handling for Chat: show File Search and URL Context fields only when Gemini provider is selected
    if (nodeType === 'chat' && normalizedProvider === 'gemini') {
      if (key === 'gemini_use_file_search') {
        // Always show the toggle when Gemini is selected
      } else if (key.startsWith('gemini_file_search')) {
        if (!formValues.gemini_use_file_search) {
          return false;
        }
      }
      // URL Context fields are handled by special handler, but ensure they show for Gemini
      if (key === 'gemini_use_url_context') {
        // Always show the toggle when Gemini is selected
      } else if (key === 'gemini_url_context_urls') {
        if (!formValues.gemini_use_url_context) {
          return false;
        }
      }
    }
    
    // Hide Gemini-specific fields when NOT using Gemini provider
    // BUT exclude special fields that have their own visibility logic
    const geminiSpecialFields = ['gemini_use_url_context', 'gemini_url_context_urls', 'gemini_use_file_search'];
    if (nodeType === 'chat' && normalizedProvider !== 'gemini' && key.startsWith('gemini_') && !geminiSpecialFields.includes(key)) {
      return false;
    }
    
    const belongsToOtherProvider = Object.entries(providerPrefixes).some(([provider, prefixes]) => {
      const normalizedProv = provider === 'google' ? 'gemini' : provider;
      if (normalizedProv === normalizedProvider) return false;
      if (currentProviderValue === 'gemini_file_search' && provider !== 'gemini_file_search') {
        return false;
      }
      return prefixes.some(prefix => key.startsWith(prefix));
    });
    
    if (belongsToOtherProvider && currentProviderValue !== 'gemini_file_search') {
      return false;
    }
    
    const isCommonField = !Object.values(providerPrefixes).flat().some(prefix => key.startsWith(prefix));
    const isCurrentProviderField = currentPrefixes.some(prefix => key.startsWith(prefix));
    const isGeminiFileSearchField = currentProviderValue === 'gemini_file_search' && key.startsWith('gemini_');
    
    if (!isCommonField && !isCurrentProviderField && !isGeminiFileSearchField) {
      return false;
    }
  }

  return true;
}

