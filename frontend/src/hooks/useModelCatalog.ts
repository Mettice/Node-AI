/**
 * Model options for a provider, from the backend model registry.
 *
 * The backend hides models the provider has shut down and lists the current
 * generation first, so forms never need their own hardcoded model lists.
 */

import { useQuery } from '@tanstack/react-query';
import { getBaseModels, type BaseModelsResponse } from '@/services/promptPlayground';

export type ModelType = 'llm' | 'embedding' | 'reranking';

export interface ModelOption {
  value: string;
  label: string;
  deprecated: boolean;
}

function toOptions(data: BaseModelsResponse | undefined): ModelOption[] {
  return (data?.models ?? []).map((model) => {
    const lifecycle = model.lifecycle;
    const deprecated = lifecycle?.status === 'deprecated';
    let label = model.model_id;
    if (deprecated) {
      label += lifecycle?.shutdown_date
        ? ` (deprecated, shuts down ${lifecycle.shutdown_date})`
        : ' (deprecated)';
    }
    return { value: model.model_id, label, deprecated };
  });
}

export function useModelCatalog(provider: string, modelType: ModelType = 'llm') {
  const query = useQuery({
    queryKey: ['model-catalog', provider, modelType],
    queryFn: () => getBaseModels(provider, modelType),
    staleTime: 60 * 60 * 1000, // the catalog changes with deploys, not during a session
    enabled: Boolean(provider),
  });

  return {
    options: toOptions(query.data),
    defaultModel: query.data?.default ?? undefined,
    isLoading: query.isLoading,
    error: query.error,
  };
}

/**
 * Options for a <select>, keeping a saved value visible even if the catalog no
 * longer offers it (e.g. a retired model); the backend upgrades it at run time.
 */
export function withCurrentValue(options: ModelOption[], value: string | undefined): ModelOption[] {
  if (!value || options.some((option) => option.value === value)) return options;
  return [{ value, label: `${value} (no longer offered, upgraded when run)`, deprecated: true }, ...options];
}
