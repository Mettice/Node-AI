/**
 * Field renderers for SchemaForm
 * Handles rendering of standard and special field types
 */

import React from 'react';
import { FormField } from '../FormField';
import { SearchProviderSelector } from '../SearchProviderSelector';
import { DatabaseSelector } from '../DatabaseSelector';
import { LanguageSelector } from '../LanguageSelector';
import { ConnectionStringInput } from '../ConnectionStringInput';
import { S3ActionSelector } from '../S3ActionSelector';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import { testDatabaseConnection } from '@/services/nodes';
import { getSpecialFieldHandler } from './FieldHandlers';

interface FieldRendererContext {
  key: string;
  fieldSchema: any;
  formValues: Record<string, any>;
  setValue: (key: string, value: any) => void;
  required: string[];
  nodeType: string;
  isToolNode: boolean;
  control: any;
}

/**
 * Render a field based on its type and context
 */
export function renderField(context: FieldRendererContext): React.ReactNode | null {
  const { key, fieldSchema, formValues, setValue, required, nodeType, isToolNode, control } = context;

  // Try special field handlers first
  const specialHandler = getSpecialFieldHandler({
    key,
    fieldSchema,
    formValues,
    setValue,
    required,
    nodeType,
    isToolNode,
  });

  if (specialHandler !== null) {
    return specialHandler;
  }

  // Special handling for web_search_provider in tool nodes
  if (isToolNode && key === 'web_search_provider') {
    return (
      <SearchProviderSelector
        key={key}
        currentProvider={formValues[key] || 'duckduckgo'}
        onChange={(provider) => setValue(key, provider)}
      />
    );
  }

  // Special handling for database_type in tool nodes
  if (isToolNode && key === 'database_type') {
    return (
      <DatabaseSelector
        key={key}
        currentDatabase={formValues[key] || 'sqlite'}
        onChange={(database) => setValue(key, database)}
      />
    );
  }

  // Special handling for database_connection_string in tool nodes
  if (isToolNode && key === 'database_connection_string') {
    return (
      <ConnectionStringInput
        key={key}
        value={formValues[key] || ''}
        onChange={(value) => setValue(key, value)}
        placeholder={fieldSchema.description || 'Enter connection string...'}
        label={fieldSchema.title || key}
        description={fieldSchema.description}
        required={required.includes(key)}
        databaseType={formValues.database_type || 'sqlite'}
        testConnection={async (connectionString: string, dbType: string) => {
          return await testDatabaseConnection(dbType, connectionString);
        }}
      />
    );
  }

  // Special handling for code_execution_language in tool nodes
  if (isToolNode && key === 'code_execution_language') {
    return (
      <LanguageSelector
        key={key}
        currentLanguage={formValues[key] || 'python'}
        onChange={(language) => setValue(key, language)}
      />
    );
  }

  // Special handling for s3_action in tool nodes
  if (isToolNode && key === 's3_action') {
    return (
      <S3ActionSelector
        key={key}
        currentAction={formValues[key] || 'list'}
        onChange={(action) => setValue(key, action)}
      />
    );
  }

  // Special handling for model fields in LLM nodes (add icons and proper formatting)
  // This applies to: langchain_agent, chat, vision, and any node with LLM provider config
  if (key === 'openai_model' || key === 'anthropic_model' || key === 'gemini_model' || key === 'azure_openai_deployment') {
    const provider = formValues.provider || 'openai';
    const iconMap: Record<string, string> = {
      'openai_model': 'openai',
      'anthropic_model': 'anthropic',
      'gemini_model': 'gemini',
      'azure_openai_deployment': 'microsoftazure',
    };
    const icon = iconMap[key] || provider;
    
    // Only show if it matches the selected provider
    if (
      (key === 'openai_model' && provider !== 'openai' && provider !== 'azure_openai') ||
      (key === 'anthropic_model' && provider !== 'anthropic') ||
      (key === 'gemini_model' && provider !== 'gemini' && provider !== 'google') || // Keep 'google' for backward compatibility
      (key === 'azure_openai_deployment' && provider !== 'azure_openai')
    ) {
      return null;
    }

    // Format model names for better display
    const formatModelName = (val: string): string => {
      return val
        .replace(/^gpt-4o-mini/i, 'GPT 4o Mini')
        .replace(/^gpt-4o/i, 'GPT 4o')
        .replace(/^gpt-4-turbo/i, 'GPT 4 Turbo')
        .replace(/^gpt-4/i, 'GPT 4')
        .replace(/^gpt-3.5-turbo/i, 'GPT 3.5 Turbo')
        .replace(/^gpt-3.5/i, 'GPT 3.5')
        .replace(/^o1-preview/i, 'O1 Preview')
        .replace(/^o1-mini/i, 'O1 Mini')
        .replace(/^o1/i, 'O1')
        .replace(/^claude-3-5-sonnet/i, 'Claude 3.5 Sonnet')
        .replace(/^claude-3-5-haiku/i, 'Claude 3.5 Haiku')
        .replace(/^claude-3-opus/i, 'Claude 3 Opus')
        .replace(/^claude-3-sonnet/i, 'Claude 3 Sonnet')
        .replace(/^claude-3-haiku/i, 'Claude 3 Haiku')
        .replace(/^claude-3/i, 'Claude 3')
        .replace(/^claude-sonnet-4-5/i, 'Claude Sonnet 4.5')
        .replace(/^claude/i, 'Claude')
        .replace(/^gemini-2.0-flash-exp/i, 'Gemini 2.0 Flash Exp')
        .replace(/^gemini-2.0-flash/i, 'Gemini 2.0 Flash')
        .replace(/^gemini-1.5-pro/i, 'Gemini 1.5 Pro')
        .replace(/^gemini-1.5-flash/i, 'Gemini 1.5 Flash')
        .replace(/^gemini-1.5/i, 'Gemini 1.5')
        .replace(/^gemini-2.5-flash/i, 'Gemini 2.5 Flash')
        .replace(/^gemini/i, 'Gemini')
        .replace(/-/g, ' ')
        .replace(/\b\w/g, (l) => l.toUpperCase());
    };

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
          value={formValues[key] || fieldSchema.default || ''}
          onChange={(value: string) => setValue(key, value)}
          options={(fieldSchema.enum || []).map((val: string) => ({
            value: val,
            label: formatModelName(val),
            icon: icon,
          }))}
          placeholder="Select a model..."
        />
      </div>
    );
  }

  // Special handling for array fields with nested objects (agents, tasks)
  if (fieldSchema.type === 'array' && fieldSchema.items && fieldSchema.items.type === 'object') {
    const currentValue = formValues[key];
    const jsonValue = Array.isArray(currentValue) 
      ? JSON.stringify(currentValue, null, 2)
      : (typeof currentValue === 'string' ? currentValue : '[]');
    
    return (
      <div key={key} className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          {fieldSchema.title || key}
          {required.includes(key) && <span className="text-red-400 ml-1">*</span>}
        </label>
        {fieldSchema.description && (
          <p className="text-xs text-slate-400 -mt-1">{fieldSchema.description}</p>
        )}
        <textarea
          value={jsonValue}
          onChange={(e) => {
            try {
              const parsed = JSON.parse(e.target.value);
              setValue(key, parsed);
            } catch {
              // Invalid JSON, store as string for now
              setValue(key, e.target.value);
            }
          }}
          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all font-mono text-sm"
          rows={8}
          placeholder={`Enter JSON array, e.g.:\n[\n  {\n    "role": "Researcher",\n    "goal": "Research the topic",\n    "backstory": "You are a research expert"\n  }\n]`}
        />
        <p className="text-xs text-slate-500">
          Enter as JSON array. Invalid JSON will be stored as text.
        </p>
      </div>
    );
  }

  // Default: use FormField
  return (
    <FormField
      key={key}
      name={key}
      schema={fieldSchema}
      required={required.includes(key)}
      control={control}
    />
  );
}

