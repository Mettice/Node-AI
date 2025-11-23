/**
 * Advanced NLP Node Form Component
 * 
 * Handles configuration for the Advanced NLP node with dynamic form fields
 * based on selected task type and provider.
 */

import { useState, useEffect, useRef } from 'react';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import { APIKeyInputWithVault } from './APIKeyInputWithVault';
import { testLLMConnection } from '@/services/nodes';

interface AdvancedNLPFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
}

const TASK_OPTIONS = [
  { value: 'summarization', label: 'Summarization', icon: 'file-text' },
  { value: 'ner', label: 'Named Entity Recognition', icon: 'tag' },
  { value: 'classification', label: 'Classification', icon: 'layers' },
  { value: 'extraction', label: 'Extraction', icon: 'extract' },
  { value: 'sentiment', label: 'Sentiment Analysis', icon: 'smile' },
  { value: 'qa', label: 'Question Answering', icon: 'help-circle' },
  { value: 'translation', label: 'Translation', icon: 'languages' },
];

const PROVIDER_OPTIONS = [
  { value: 'huggingface', label: 'HuggingFace', icon: 'huggingface' },
  { value: 'openai', label: 'OpenAI', icon: 'openai' },
  { value: 'anthropic', label: 'Anthropic', icon: 'anthropic' },
  { value: 'azure', label: 'Azure', icon: 'microsoftazure' },
  { value: 'custom', label: 'Custom API', icon: 'code' },
];

export function AdvancedNLPForm({ initialData, onChange }: AdvancedNLPFormProps) {
  const [taskType, setTaskType] = useState(initialData.task_type || 'summarization');
  const [provider, setProvider] = useState(initialData.provider || 'huggingface');
  
  // Task-specific fields
  const [maxLength, setMaxLength] = useState(initialData.max_length || 150);
  const [minLength, setMinLength] = useState(initialData.min_length || 30);
  const [categories, setCategories] = useState<string[]>(initialData.categories || []);
  const [categoryInput, setCategoryInput] = useState('');
  const [extractionSchemaText, setExtractionSchemaText] = useState(
    JSON.stringify(initialData.extraction_schema || {}, null, 2)
  );
  const [question, setQuestion] = useState(initialData.question || '');
  const [sourceLanguage, setSourceLanguage] = useState(initialData.source_language || 'auto');
  const [targetLanguage, setTargetLanguage] = useState(initialData.target_language || 'en');
  
  // Provider-specific fields
  const [hfModel, setHfModel] = useState(initialData.hf_model || '');
  const [openaiApiKey, setOpenaiApiKey] = useState(initialData.openai_api_key || '');
  const [openaiModel, setOpenaiModel] = useState(initialData.openai_model || 'gpt-4o-mini');
  const [openaiSecretId, setOpenaiSecretId] = useState(initialData.openai_api_key_secret_id || '');
  const [anthropicApiKey, setAnthropicApiKey] = useState(initialData.anthropic_api_key || '');
  const [anthropicModel, setAnthropicModel] = useState(initialData.anthropic_model || 'claude-sonnet-4-5-20250929');
  const [anthropicSecretId, setAnthropicSecretId] = useState(initialData.anthropic_api_key_secret_id || '');
  
  // Custom API and caching
  const [customApiUrl, setCustomApiUrl] = useState(initialData.custom_api_url || '');
  const [customApiKey, setCustomApiKey] = useState(initialData.custom_api_key || '');
  const [customApiMethod, setCustomApiMethod] = useState(initialData.custom_api_method || 'POST');
  const [enableCache, setEnableCache] = useState(initialData.enable_cache !== false);
  const [cacheTtl, setCacheTtl] = useState(initialData.cache_ttl_seconds || 3600);
  const [useFinetunedModel, setUseFinetunedModel] = useState(initialData.use_finetuned_model || false);
  const [finetunedModelId, setFinetunedModelId] = useState(initialData.finetuned_model_id || '');
  
  const onChangeRef = useRef(onChange);
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  // Update parent when form changes
  useEffect(() => {
    const config: Record<string, any> = {
      task_type: taskType,
      provider,
    };

    // Task-specific config
    if (taskType === 'summarization') {
      config.max_length = maxLength;
      config.min_length = minLength;
    } else if (taskType === 'classification') {
      config.categories = categories;
    } else if (taskType === 'extraction') {
      try {
        config.extraction_schema = JSON.parse(extractionSchemaText);
      } catch (e) {
        // Invalid JSON, skip for now
      }
    } else if (taskType === 'qa') {
      config.question = question;
    } else if (taskType === 'translation') {
      config.source_language = sourceLanguage;
      config.target_language = targetLanguage;
    }

    // Provider-specific config
    if (provider === 'huggingface' && hfModel) {
      config.hf_model = hfModel;
    } else if (provider === 'openai') {
      if (openaiApiKey) {
        config.openai_api_key = openaiApiKey;
        if (openaiSecretId) {
          config.openai_api_key_secret_id = openaiSecretId;
        }
      }
      config.openai_model = openaiModel;
    } else if (provider === 'anthropic') {
      if (anthropicApiKey) {
        config.anthropic_api_key = anthropicApiKey;
        if (anthropicSecretId) {
          config.anthropic_api_key_secret_id = anthropicSecretId;
        }
      }
      config.anthropic_model = anthropicModel;
    } else if (provider === 'custom') {
      if (customApiUrl) {
        config.custom_api_url = customApiUrl;
      }
      if (customApiKey) {
        config.custom_api_key = customApiKey;
      }
      config.custom_api_method = customApiMethod;
    }

    // Caching and fine-tuned model config
    config.enable_cache = enableCache;
    config.cache_ttl_seconds = cacheTtl;
    config.use_finetuned_model = useFinetunedModel;
    if (useFinetunedModel && finetunedModelId) {
      config.finetuned_model_id = finetunedModelId;
    }

    const timeoutId = setTimeout(() => {
      onChangeRef.current(config);
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [
    taskType,
    provider,
    maxLength,
    minLength,
    categories,
    extractionSchemaText,
    question,
    sourceLanguage,
    targetLanguage,
    hfModel,
    openaiApiKey,
    openaiModel,
    openaiSecretId,
    anthropicApiKey,
    anthropicModel,
    anthropicSecretId,
    customApiUrl,
    customApiKey,
    customApiMethod,
    enableCache,
    cacheTtl,
    useFinetunedModel,
    finetunedModelId,
  ]);

  const addCategory = () => {
    if (categoryInput.trim()) {
      setCategories([...categories, categoryInput.trim()]);
      setCategoryInput('');
    }
  };

  const removeCategory = (index: number) => {
    setCategories(categories.filter((_, i) => i !== index));
  };

  const languageOptions = [
    { value: 'auto', label: 'Auto-detect' },
    { value: 'en', label: 'English' },
    { value: 'es', label: 'Spanish' },
    { value: 'fr', label: 'French' },
    { value: 'de', label: 'German' },
    { value: 'it', label: 'Italian' },
    { value: 'pt', label: 'Portuguese' },
    { value: 'zh', label: 'Chinese' },
    { value: 'ja', label: 'Japanese' },
    { value: 'ko', label: 'Korean' },
  ];

  return (
    <div className="space-y-6">
      {/* Task Type Selection */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">
          NLP Task <span className="text-red-400">*</span>
        </label>
        <SelectWithIcons
          value={taskType}
          onChange={setTaskType}
          options={TASK_OPTIONS}
          placeholder="Select a task..."
        />
      </div>

      {/* Provider Selection */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">
          Provider <span className="text-red-400">*</span>
        </label>
        <SelectWithIcons
          value={provider}
          onChange={setProvider}
          options={PROVIDER_OPTIONS}
          placeholder="Select a provider..."
        />
      </div>

      {/* Summarization Config */}
      {taskType === 'summarization' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Max Length: {maxLength}
            </label>
            <input
              type="range"
              min="10"
              max="1000"
              value={maxLength}
              onChange={(e) => setMaxLength(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-slate-400 mt-1">Maximum length for summary</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Min Length: {minLength}
            </label>
            <input
              type="range"
              min="5"
              max="500"
              value={minLength}
              onChange={(e) => setMinLength(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-slate-400 mt-1">Minimum length for summary</p>
          </div>
        </div>
      )}

      {/* Classification Config */}
      {taskType === 'classification' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">Categories</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={categoryInput}
                onChange={(e) => setCategoryInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addCategory()}
                placeholder="Enter category and press Enter"
                className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <button
                onClick={addCategory}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
              >
                Add
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-1">Add categories to classify text into</p>
          </div>
          {categories.length > 0 && (
            <div>
              <div className="flex flex-wrap gap-2">
                {categories.map((cat, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-2 px-3 py-1 bg-slate-700 rounded-lg text-sm"
                  >
                    {cat}
                    <button
                      onClick={() => removeCategory(index)}
                      className="text-red-400 hover:text-red-300"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Extraction Config */}
      {taskType === 'extraction' && (
        <div>
          <label className="block text-sm font-medium text-white mb-2">Extraction Schema (JSON)</label>
          <textarea
            value={extractionSchemaText}
            onChange={(e) => setExtractionSchemaText(e.target.value)}
            placeholder='{"name": "string", "age": "number", "email": "string"}'
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm"
            rows={6}
          />
          <p className="text-xs text-slate-400 mt-1">JSON schema defining what to extract</p>
        </div>
      )}

      {/* Question Answering Config */}
      {taskType === 'qa' && (
        <div>
          <label className="block text-sm font-medium text-white mb-2">Question</label>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your question..."
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <p className="text-xs text-slate-400 mt-1">Question to answer based on the input text</p>
        </div>
      )}

      {/* Translation Config */}
      {taskType === 'translation' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">Source Language</label>
            <select
              value={sourceLanguage}
              onChange={(e) => setSourceLanguage(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              {languageOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">Target Language</label>
            <select
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              {languageOptions.filter((opt) => opt.value !== 'auto').map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* HuggingFace Config */}
      {provider === 'huggingface' && (
        <div>
          <label className="block text-sm font-medium text-white mb-2">HuggingFace Model (Optional)</label>
          <input
            type="text"
            value={hfModel}
            onChange={(e) => setHfModel(e.target.value)}
            placeholder="Leave empty to use default model for task"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <p className="text-xs text-slate-400 mt-1">Custom HuggingFace model name (e.g., facebook/bart-large-cnn)</p>
        </div>
      )}

      {/* OpenAI Config */}
      {provider === 'openai' && (
        <div className="space-y-4">
          <APIKeyInputWithVault
            value={openaiApiKey}
            onChange={(value, secretId) => {
              setOpenaiApiKey(value);
              setOpenaiSecretId(secretId || '');
            }}
            placeholder="Enter OpenAI API key..."
            label="OpenAI API Key"
            description="Optional: OpenAI API key (uses environment variable if not provided)"
            serviceName="OpenAI"
            provider="openai"
            testConnection={async (apiKey: string) => {
              return await testLLMConnection('openai', apiKey);
            }}
          />
          <div>
            <label className="block text-sm font-medium text-white mb-2">OpenAI Model</label>
            <input
              type="text"
              value={openaiModel}
              onChange={(e) => setOpenaiModel(e.target.value)}
              placeholder="gpt-4o-mini"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>
      )}

      {/* Anthropic Config */}
      {provider === 'anthropic' && (
        <div className="space-y-4">
          <APIKeyInputWithVault
            value={anthropicApiKey}
            onChange={(value, secretId) => {
              setAnthropicApiKey(value);
              setAnthropicSecretId(secretId || '');
            }}
            placeholder="Enter Anthropic API key..."
            label="Anthropic API Key"
            description="Optional: Anthropic API key (uses environment variable if not provided)"
            serviceName="Anthropic"
            provider="anthropic"
            testConnection={async (apiKey: string) => {
              return await testLLMConnection('anthropic', apiKey);
            }}
          />
          <div>
            <label className="block text-sm font-medium text-white mb-2">Anthropic Model</label>
            <input
              type="text"
              value={anthropicModel}
              onChange={(e) => setAnthropicModel(e.target.value)}
              placeholder="claude-sonnet-4-5-20250929"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>
      )}

      {/* Azure Config */}
      {provider === 'azure' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">Azure Text Analytics Endpoint</label>
            <input
              type="text"
              value={initialData.azure_text_analytics_endpoint || ''}
              onChange={(e) => {
                const config: Record<string, any> = { ...initialData, azure_text_analytics_endpoint: e.target.value };
                onChange(config);
              }}
              placeholder="https://your-resource.cognitiveservices.azure.com/"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <p className="text-xs text-slate-400 mt-1">For NER and Sentiment Analysis</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">Azure Text Analytics API Key</label>
            <input
              type="password"
              value={initialData.azure_text_analytics_api_key || ''}
              onChange={(e) => {
                const config: Record<string, any> = { ...initialData, azure_text_analytics_api_key: e.target.value };
                onChange(config);
              }}
              placeholder="Enter API key..."
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">Azure Translator Endpoint</label>
            <input
              type="text"
              value={initialData.azure_translator_endpoint || ''}
              onChange={(e) => {
                const config: Record<string, any> = { ...initialData, azure_translator_endpoint: e.target.value };
                onChange(config);
              }}
              placeholder="https://api.cognitive.microsofttranslator.com"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <p className="text-xs text-slate-400 mt-1">For Translation</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">Azure Translator API Key</label>
            <input
              type="password"
              value={initialData.azure_translator_api_key || ''}
              onChange={(e) => {
                const config: Record<string, any> = { ...initialData, azure_translator_api_key: e.target.value };
                onChange(config);
              }}
              placeholder="Enter API key..."
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>
      )}

      {/* Custom API Config */}
      {provider === 'custom' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">API URL <span className="text-red-400">*</span></label>
            <input
              type="text"
              value={customApiUrl}
              onChange={(e) => setCustomApiUrl(e.target.value)}
              placeholder="https://api.example.com/nlp"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <p className="text-xs text-slate-400 mt-1">Custom API endpoint URL</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">API Key</label>
            <input
              type="password"
              value={customApiKey}
              onChange={(e) => setCustomApiKey(e.target.value)}
              placeholder="Enter API key (optional)"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">HTTP Method</label>
            <select
              value={customApiMethod}
              onChange={(e) => setCustomApiMethod(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="POST">POST</option>
              <option value="GET">GET</option>
            </select>
          </div>
        </div>
      )}

      {/* Fine-tuned Model Config */}
      <div className="space-y-4 border-t border-slate-700 pt-4">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="use_finetuned"
            checked={useFinetunedModel}
            onChange={(e) => setUseFinetunedModel(e.target.checked)}
            className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-purple-600 focus:ring-purple-500"
          />
          <label htmlFor="use_finetuned" className="text-sm font-medium text-white">
            Use Fine-Tuned Model
          </label>
        </div>
        {useFinetunedModel && (
          <div>
            <label className="block text-sm font-medium text-white mb-2">Fine-Tuned Model ID</label>
            <input
              type="text"
              value={finetunedModelId}
              onChange={(e) => setFinetunedModelId(e.target.value)}
              placeholder="Enter model ID from registry"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <p className="text-xs text-slate-400 mt-1">ID of the fine-tuned model from the model registry</p>
          </div>
        )}
      </div>

      {/* Caching Config */}
      <div className="space-y-4 border-t border-slate-700 pt-4">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="enable_cache"
            checked={enableCache}
            onChange={(e) => setEnableCache(e.target.checked)}
            className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-purple-600 focus:ring-purple-500"
          />
          <label htmlFor="enable_cache" className="text-sm font-medium text-white">
            Enable Result Caching
          </label>
        </div>
        {enableCache && (
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Cache TTL: {cacheTtl} seconds ({Math.round(cacheTtl / 60)} minutes)
            </label>
            <input
              type="range"
              min="0"
              max="86400"
              step="300"
              value={cacheTtl}
              onChange={(e) => setCacheTtl(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-slate-400 mt-1">Time to live for cached results (0 = no expiration)</p>
          </div>
        )}
      </div>
    </div>
  );
}

