/**
 * Model dropdown backed by the backend model registry.
 *
 * Fills in the provider's default model when no model is set, so the form shows the
 * model the backend will actually use.
 */

import { useEffect } from 'react';
import { useModelCatalog, withCurrentValue, type ModelType } from '@/hooks/useModelCatalog';

interface ModelSelectProps {
  provider: string;
  value: string | undefined;
  onChange: (model: string) => void;
  modelType?: ModelType;
  className?: string;
  id?: string;
}

const DEFAULT_CLASS =
  'w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500';

export function ModelSelect({ provider, value, onChange, modelType = 'llm', className, id }: ModelSelectProps) {
  const { options, defaultModel, isLoading, error } = useModelCatalog(provider, modelType);

  useEffect(() => {
    if (!value && defaultModel) onChange(defaultModel);
  }, [value, defaultModel, onChange]);

  if (error) {
    // Catalog unavailable: keep the field editable rather than blocking the form
    return (
      <input
        id={id}
        className={className ?? DEFAULT_CLASS}
        value={value ?? ''}
        placeholder="Model ID"
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  return (
    <select
      id={id}
      className={className ?? DEFAULT_CLASS}
      value={value ?? ''}
      disabled={isLoading && !value}
      onChange={(event) => onChange(event.target.value)}
    >
      {isLoading && !value && <option value="">Loading models…</option>}
      {withCurrentValue(options, value).map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
