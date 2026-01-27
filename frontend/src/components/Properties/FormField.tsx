/**
 * Individual form field component
 */

import { Controller } from 'react-hook-form';
import type { Control } from 'react-hook-form';
import { Input } from '@/components/common/Input';
import { Select } from '@/components/common/Select';

interface FormFieldProps {
  name: string;
  schema: any;
  required?: boolean;
  control: Control<any>;
}

export function FormField({ name, schema, required, control }: FormFieldProps) {
  const label = schema.title || name;
  const description = schema.description;
  const fieldType = schema.type;

  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
        {label}
        {required && <span className="text-red-400 ml-1">*</span>}
      </label>
      
      {description && (
        <p className="text-xs text-slate-400 -mt-1">{description}</p>
      )}

      <Controller
        name={name}
        control={control}
        rules={{ required }}
              render={({ field, fieldState }) => (
                <>
                  {fieldType === 'string' && schema.enum ? (
                    <Select
                      {...field}
                      options={schema.enum.map((val: string) => {
                        // Format model names for better readability
                        let label = val;
                        if (name.includes('model') || name.includes('voyage_model') || name.includes('cohere_model') || name.includes('gemini_model')) {
                          // Format model names: "embed-v4.0" -> "Embed v4.0"
                          label = val
                            .replace(/^embed-/, 'Embed ')
                            .replace(/^rerank-/, 'Rerank ')
                            .replace(/^voyage-/, 'Voyage ')
                            .replace(/^gemini-/, 'Gemini ')
                            .replace(/^text-embedding-/, 'Text Embedding ')
                            .replace(/-/g, ' ')
                            .replace(/\b\w/g, (l) => l.toUpperCase());
                        } else if (name.includes('task_type')) {
                          // Format task type enum values for better readability
                          // "SEMANTIC_SIMILARITY" -> "Semantic Similarity"
                          label = val
                            .replace(/_/g, ' ')
                            .replace(/\b\w/g, (l) => l.toUpperCase());
                        }
                        return {
                          value: val,
                          label: label,
                        };
                      })}
                      error={fieldState.error?.message}
                    />
                  ) : fieldType === 'string' ? (
                    <Input
                      {...field}
                      type="text"
                      placeholder={schema.default || ''}
                      error={fieldState.error?.message}
                    />
                  ) : fieldType === 'number' || fieldType === 'integer' ? (
                    <Input
                      {...field}
                      type="number"
                      min={schema.minimum}
                      max={schema.maximum}
                      step={fieldType === 'integer' ? 1 : undefined}
                      placeholder={schema.default?.toString() || ''}
                      error={fieldState.error?.message}
                      onChange={(e) => {
                        // Convert string to number
                        const value = e.target.value;
                        if (value === '') {
                          field.onChange(undefined);
                        } else {
                          const numValue = fieldType === 'integer' 
                            ? parseInt(value, 10) 
                            : parseFloat(value);
                          field.onChange(isNaN(numValue) ? value : numValue);
                        }
                      }}
                    />
                  ) : fieldType === 'boolean' ? (
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={field.value || false}
                        onChange={(e) => field.onChange(e.target.checked)}
                        className="h-4 w-4 text-amber-500 focus:ring-amber-500 border-white/20 rounded bg-white/5"
                      />
                      <span className="ml-2 text-sm text-slate-300">
                        {schema.description || 'Enable'}
                      </span>
                    </div>
                  ) : (
                    <Input
                      {...field}
                      type="text"
                      placeholder={schema.default || ''}
                      error={fieldState.error?.message}
                    />
                  )}
                  {fieldState.error && (
                    <p className="text-xs text-red-400 mt-1">
                      {fieldState.error.message}
                    </p>
                  )}
                </>
              )}
      />
    </div>
  );
}

