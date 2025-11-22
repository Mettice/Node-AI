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

  // Special handling for model fields in langchain_agent, chat, and vision (add icons)
  if ((nodeType === 'langchain_agent' || nodeType === 'chat' || nodeType === 'vision') && 
      (key === 'openai_model' || key === 'anthropic_model' || key === 'gemini_model')) {
    const provider = formValues.provider || 'openai';
    const iconMap: Record<string, string> = {
      'openai_model': 'openai',
      'anthropic_model': 'anthropic',
      'gemini_model': 'gemini',
    };
    const icon = iconMap[key] || provider;
    
    // Only show if it matches the selected provider
    if (
      (key === 'openai_model' && provider !== 'openai') ||
      (key === 'anthropic_model' && provider !== 'anthropic') ||
      (key === 'gemini_model' && provider !== 'gemini' && provider !== 'google') // Keep 'google' for backward compatibility
    ) {
      return null;
    }

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
            label: val
              .replace(/^gpt-/, 'GPT-')
              .replace(/^o1-/, 'O1-')
              .replace(/^claude-/, 'Claude ')
              .replace(/^gemini-/, 'Gemini ')
              .replace(/-/g, ' ')
              .replace(/\b\w/g, (l) => l.toUpperCase()),
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
          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all font-mono text-sm"
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

