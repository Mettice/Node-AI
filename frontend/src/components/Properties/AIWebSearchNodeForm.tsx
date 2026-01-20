/**
 * AI Web Search Node Form
 * Custom form for AI Web Search node with provider selection and conditional fields
 */

import { useForm, Controller } from 'react-hook-form';
import { useEffect } from 'react';
import { APIKeyInputWithVault } from './APIKeyInputWithVault';
import { ProviderSelector } from './ProviderSelector';

interface AIWebSearchNodeFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
}

export function AIWebSearchNodeForm({
  initialData,
  onChange,
}: AIWebSearchNodeFormProps) {
  const { control, watch, setValue } = useForm({
    defaultValues: {
      query: initialData.query || '',
      provider: initialData.provider || 'perplexity', // Search provider
      perplexity_api_key: initialData.perplexity_api_key || '',
      tavily_api_key: initialData.tavily_api_key || '',
      serper_api_key: initialData.serper_api_key || '',
      perplexity_model: initialData.perplexity_model || 'sonar',
      max_tokens: initialData.max_tokens || 1000,
      max_results: initialData.max_results || 5,
      search_depth: initialData.search_depth || 'basic',
      enhance_with_llm: initialData.enhance_with_llm || false,
      // LLM config (if enhancement enabled) - use llm_provider to avoid conflict
      llm_provider: initialData.llm_provider || initialData.provider || 'openai',
      openai_model: initialData.openai_model || 'gpt-4o-mini',
      anthropic_model: initialData.anthropic_model || 'claude-sonnet-4-5-20250929',
      gemini_model: initialData.gemini_model || 'gemini-2.5-flash',
      temperature: initialData.temperature || 0.1,
    },
  });

  const formValues = watch();
  const searchProvider = watch('provider'); // Search provider (perplexity/tavily/serper)
  const enhanceWithLLM = watch('enhance_with_llm');
  const llmProvider = watch('llm_provider') || 'openai'; // LLM provider for enhancement

  // Update parent on form change
  useEffect(() => {
    const subscription = watch((value) => {
      // Clean up undefined/empty values
      const cleaned = Object.entries(value).reduce((acc, [key, val]) => {
        if (val !== undefined && val !== '' && val !== null) {
          acc[key] = val;
        }
        return acc;
      }, {} as Record<string, any>);

      // Handle provider conflict: backend uses 'provider' for both search and LLM
      // Store search provider separately when LLM enhancement is enabled
      if (cleaned.enhance_with_llm && cleaned.llm_provider) {
        // Save search provider before overwriting
        const searchProvider = cleaned.provider; // This is the search provider (perplexity/tavily/serper)
        cleaned.search_provider = searchProvider; // Store it separately
        cleaned.provider = cleaned.llm_provider; // LLM provider for LLMConfigMixin
        delete cleaned.llm_provider; // Remove the temporary field
      }
      // When enhance_with_llm is false, provider is the search provider (already set)

      onChange(cleaned);
    });
    return () => subscription.unsubscribe();
  }, [watch, onChange]);

  return (
    <div className="space-y-6">
      {/* Search Query */}
      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          Search Query <span className="text-red-400">*</span>
        </label>
        <p className="text-xs text-slate-400 -mt-1">
          The search query to execute (can also be provided via inputs)
        </p>
        <Controller
          name="query"
          control={control}
          render={({ field }) => (
            <textarea
              {...field}
              rows={3}
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
              placeholder="Enter your search query..."
            />
          )}
        />
      </div>

      {/* Search Provider Selection */}
      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          Search Provider <span className="text-red-400">*</span>
        </label>
        <p className="text-xs text-slate-400 -mt-1">
          AI search provider to use. Perplexity is recommended for best results.
        </p>
        <Controller
          name="provider"
          control={control}
          render={({ field }) => (
            <select
              {...field}
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
            >
              <option value="perplexity">Perplexity AI (Recommended)</option>
              <option value="tavily">Tavily AI Search</option>
              <option value="serper">Serper (Google Search)</option>
            </select>
          )}
        />
      </div>

      {/* Conditional API Key Fields */}
      {searchProvider === 'perplexity' && (
        <div className="space-y-4">
          <Controller
            name="perplexity_api_key"
            control={control}
            render={({ field }) => (
              <APIKeyInputWithVault
                value={field.value || ''}
                onChange={(value) => field.onChange(value)}
                label="Perplexity API Key"
                description="API key for Perplexity AI. Get one at https://www.perplexity.ai/"
                required
                provider="perplexity"
              />
            )}
          />
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Perplexity Model
            </label>
            <Controller
              name="perplexity_model"
              control={control}
              render={({ field }) => (
                <select
                  {...field}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                >
                  <option value="sonar">Sonar (Default)</option>
                  <option value="sonar-pro">Sonar Pro</option>
                  <option value="sonar-online">Sonar Online</option>
                  <option value="sonar-pro-online">Sonar Pro Online</option>
                </select>
              )}
            />
          </div>
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Max Tokens
            </label>
            <Controller
              name="max_tokens"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  type="number"
                  min={100}
                  max={4000}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                />
              )}
            />
          </div>
        </div>
      )}

      {searchProvider === 'tavily' && (
        <div className="space-y-4">
          <Controller
            name="tavily_api_key"
            control={control}
            render={({ field }) => (
              <APIKeyInputWithVault
                value={field.value || ''}
                onChange={(value) => field.onChange(value)}
                label="Tavily API Key"
                description="API key for Tavily AI Search. Get one at https://tavily.com/"
                required
                provider="tavily"
              />
            )}
          />
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Max Results
            </label>
            <Controller
              name="max_results"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  type="number"
                  min={1}
                  max={20}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                />
              )}
            />
          </div>
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Search Depth
            </label>
            <Controller
              name="search_depth"
              control={control}
              render={({ field }) => (
                <select
                  {...field}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                >
                  <option value="basic">Basic (Faster)</option>
                  <option value="advanced">Advanced (More Comprehensive)</option>
                </select>
              )}
            />
          </div>
        </div>
      )}

      {searchProvider === 'serper' && (
        <div className="space-y-4">
          <Controller
            name="serper_api_key"
            control={control}
            render={({ field }) => (
              <APIKeyInputWithVault
                value={field.value || ''}
                onChange={(value) => field.onChange(value)}
                label="Serper API Key"
                description="API key for Serper. Get one at https://serper.dev/"
                required
                provider="serper"
              />
            )}
          />
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Max Results
            </label>
            <Controller
              name="max_results"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  type="number"
                  min={1}
                  max={20}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                />
              )}
            />
          </div>
        </div>
      )}

      {/* LLM Enhancement Section */}
      <div className="pt-4 border-t border-slate-700">
        <div className="space-y-2 mb-4">
          <Controller
            name="enhance_with_llm"
            control={control}
            render={({ field }) => (
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  {...field}
                  checked={field.value || false}
                  className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-blue-500 focus:ring-2 focus:ring-blue-500/50"
                />
                <span className="text-sm text-slate-300">
                  Enhance with LLM
                </span>
              </label>
            )}
          />
          <p className="text-xs text-slate-400 ml-6">
            Use an LLM to further refine and summarize search results (requires LLM configuration)
          </p>
        </div>

        {enhanceWithLLM && (
          <div className="space-y-4 ml-6 pl-4 border-l-2 border-slate-700">
            <ProviderSelector
              nodeType="ai_web_search"
              currentProvider={llmProvider || 'openai'}
              onChange={(provider) => setValue('llm_provider', provider)}
            />
            
            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                {llmProvider === 'openai' ? 'OpenAI Model' :
                 llmProvider === 'anthropic' ? 'Anthropic Model' :
                 'Gemini Model'}
              </label>
              <Controller
                name={llmProvider === 'openai' ? 'openai_model' :
                      llmProvider === 'anthropic' ? 'anthropic_model' :
                      'gemini_model'}
                control={control}
                render={({ field }) => (
                  <select
                    {...field}
                    className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                  >
                    {llmProvider === 'openai' && (
                      <>
                        <option value="gpt-4o">GPT-4o</option>
                        <option value="gpt-4o-mini">GPT-4o Mini</option>
                        <option value="gpt-4">GPT-4</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                      </>
                    )}
                    {llmProvider === 'anthropic' && (
                      <>
                        <option value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5</option>
                        <option value="claude-opus-4-5-20251101">Claude Opus 4.5</option>
                        <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                      </>
                    )}
                    {llmProvider === 'gemini' && (
                      <>
                        <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                        <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                        <option value="gemini-3-flash-preview">Gemini 3 Flash Preview</option>
                        <option value="gemini-3-pro-preview">Gemini 3 Pro Preview</option>
                      </>
                    )}
                  </select>
                )}
              />
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Temperature
              </label>
              <Controller
                name="temperature"
                control={control}
                render={({ field }) => (
                  <input
                    {...field}
                    type="number"
                    min={0}
                    max={2}
                    step={0.1}
                    className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                  />
                )}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
