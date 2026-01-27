/**
 * Prompt Playground - Test prompts without full workflow
 */

import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useUIStore } from '@/store/uiStore';
import {
  testPrompt,
  abTestPrompts,
  listPromptVersions,
  getBaseModels,
  type PromptTestResult,
  type ABTestResult,
} from '@/services/promptPlayground';
import { Spinner } from '@/components/common/Spinner';
import { Button } from '@/components/common/Button';
import { Textarea } from '@/components/common/Textarea';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import {
  Play,
  TrendingUp,
  ArrowRight,
} from 'lucide-react';
import { cn } from '@/utils/cn';

type Tab = 'test' | 'ab-test' | 'versions';

export function PromptPlayground() {
  const { promptPlaygroundInitialPrompt, setSidebarTab } = useUIStore();
  const [activeTab, setActiveTab] = useState<Tab>('test');
  
  // Test tab state
  const [prompt, setPrompt] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [testInput, setTestInput] = useState('');
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-4o-mini');
  const [temperature, setTemperature] = useState(0.7);
  
  // Fetch available models for each provider
  const { data: openaiModels } = useQuery({
    queryKey: ['base-models', 'openai', 'llm'],
    queryFn: () => getBaseModels('openai', 'llm'),
    select: (data) => data.models,
  });
  
  const { data: anthropicModels } = useQuery({
    queryKey: ['base-models', 'anthropic', 'llm'],
    queryFn: () => getBaseModels('anthropic', 'llm'),
    select: (data) => data.models,
  });
  
  const { data: geminiModels } = useQuery({
    queryKey: ['base-models', 'gemini', 'llm'],
    queryFn: () => getBaseModels('gemini', 'llm'),
    select: (data) => data.models,
  });
  
  // Get models for current provider
  const availableModels = provider === 'openai' 
    ? (openaiModels || [])
    : provider === 'anthropic'
    ? (anthropicModels || [])
    : provider === 'gemini'
    ? (geminiModels || [])
    : [];
  
  // Get current model pricing info
  const currentModelInfo = availableModels.find(m => m.model_id === model);
  
  // Load initial prompt if provided
  useEffect(() => {
    if (promptPlaygroundInitialPrompt) {
      setPrompt(promptPlaygroundInitialPrompt);
      // Clear the initial prompt after loading
      setSidebarTab('prompt', undefined);
    }
  }, [promptPlaygroundInitialPrompt, setSidebarTab]);
  
  // A/B test state
  const [promptA, setPromptA] = useState('');
  const [promptB, setPromptB] = useState('');
  const [abTestInputs, setAbTestInputs] = useState<string[]>(['']);
  
  // Results
  const [testResult, setTestResult] = useState<PromptTestResult | null>(null);
  const [abTestResult, setAbTestResult] = useState<ABTestResult | null>(null);
  
  // Test mutation
  const testMutation = useMutation({
    mutationFn: testPrompt,
    onSuccess: (data) => {
      setTestResult(data);
    },
  });
  
  // A/B test mutation
  const abTestMutation = useMutation({
    mutationFn: abTestPrompts,
    onSuccess: (data) => {
      setAbTestResult(data);
    },
  });
  
  // Versions query
  const { data: versions } = useQuery({
    queryKey: ['prompt-versions'],
    queryFn: listPromptVersions,
  });
  
  const handleTest = () => {
    if (!prompt.trim()) return;
    
    testMutation.mutate({
      prompt,
      provider,
      model,
      system_prompt: systemPrompt || undefined,
      temperature,
      test_inputs: testInput ? [testInput] : undefined,
    });
  };
  
  const handleABTest = () => {
    if (!promptA.trim() || !promptB.trim()) return;
    
    const inputs = abTestInputs.filter(i => i.trim());
    if (inputs.length === 0) {
      inputs.push('');
    }
    
    abTestMutation.mutate({
      prompt_a: promptA,
      prompt_b: promptB,
      provider,
      model,
      system_prompt: systemPrompt || undefined,
      temperature,
      test_inputs: inputs,
    });
  };
  
  const handleExportToWorkflow = (promptText: string) => {
    // Copy to clipboard and show notification
    navigator.clipboard.writeText(promptText);
    // TODO: Could integrate with workflow store to update selected node's prompt
    // For now, user can paste it manually
  };
  
  // Update model when provider changes
  useEffect(() => {
    if (availableModels.length > 0) {
      const currentModelExists = availableModels.find(m => m.model_id === model);
      if (!currentModelExists) {
        setModel(availableModels[0].model_id);
      }
    }
  }, [provider, availableModels]);
  
  return (
    <div className="h-full flex flex-col glass-strong border-r border-white/10">
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <h2 className="text-lg font-semibold text-white mb-2">Prompt Playground</h2>
        <p className="text-sm text-slate-400">
          Test and compare prompts without running full workflows
        </p>
      </div>
      
      {/* Tabs */}
      <div className="flex border-b border-white/10 bg-slate-900/50">
        <button
          onClick={() => setActiveTab('test')}
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium transition-all flex items-center justify-center gap-1.5',
            activeTab === 'test'
              ? 'bg-amber-500/20 text-amber-300 border-b-2 border-amber-500'
              : 'text-slate-400 hover:text-slate-300 hover:bg-white/5'
          )}
        >
          Test Prompt
        </button>
        <button
          onClick={() => setActiveTab('ab-test')}
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium transition-all flex items-center justify-center gap-1.5',
            activeTab === 'ab-test'
              ? 'bg-amber-500/20 text-amber-300 border-b-2 border-amber-500'
              : 'text-slate-400 hover:text-slate-300 hover:bg-white/5'
          )}
        >
          A/B Test
        </button>
        <button
          onClick={() => setActiveTab('versions')}
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium transition-all flex items-center justify-center gap-1.5',
            activeTab === 'versions'
              ? 'bg-amber-500/20 text-amber-300 border-b-2 border-amber-500'
              : 'text-slate-400 hover:text-slate-300 hover:bg-white/5'
          )}
        >
          Versions
        </button>
      </div>
      
      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 min-w-0">
        {/* Test Tab */}
        {activeTab === 'test' && (
        <div className="space-y-4 min-w-0">
          <div className="grid grid-cols-2 gap-3 min-w-0">
            <div>
              <label className="block text-xs text-white mb-1">Provider</label>
              <SelectWithIcons
                value={provider}
                onChange={(value) => {
                  setProvider(value);
                  // Model will be updated by useEffect when availableModels changes
                }}
                options={[
                  { value: 'openai', label: 'OpenAI', icon: 'openai' },
                  { value: 'anthropic', label: 'Anthropic', icon: 'anthropic' },
                  { value: 'gemini', label: 'Google Gemini', icon: 'gemini' },
                ]}
              />
            </div>
            <div>
              <label className="block text-xs text-white mb-1">Model</label>
              {availableModels.length > 0 ? (
                <>
                  <SelectWithIcons
                    value={model}
                    onChange={(value) => setModel(value)}
                    options={availableModels.map(m => ({
                      value: m.model_id,
                      label: m.model_id
                        .replace(/^gpt-/, 'GPT-')
                        .replace(/^o1-/, 'O1-')
                        .replace(/^claude-/, 'Claude ')
                        .replace(/^gemini-/, 'Gemini ')
                        .replace(/-/g, ' ')
                        .replace(/\b\w/g, (l) => l.toUpperCase()),
                      icon: provider,
                    }))}
                  />
                  {currentModelInfo?.pricing && (
                    <div className="mt-1 text-xs text-slate-400">
                      {currentModelInfo.pricing.input_per_1k && currentModelInfo.pricing.output_per_1k && (
                        <span>
                          ${(currentModelInfo.pricing.input_per_1k * 1000).toFixed(2)}/1M in • ${(currentModelInfo.pricing.output_per_1k * 1000).toFixed(2)}/1M out
                        </span>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <div className="text-xs text-slate-400 py-2">Loading models...</div>
              )}
            </div>
          </div>
          
          <div className="min-w-0">
            <label className="block text-xs text-white mb-1">System Prompt (optional)</label>
            <Textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="You are a helpful assistant..."
              rows={2}
            />
          </div>
          
          <div className="min-w-0">
            <label className="block text-xs text-white mb-1">Prompt</label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt here. Use {input} to insert test input."
              rows={6}
            />
          </div>
          
          <div className="min-w-0">
            <label className="block text-xs text-white mb-1">Test Input (optional)</label>
            <Textarea
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              placeholder="Enter test input (will replace {input} in prompt)"
              rows={2}
            />
          </div>
          
          <div>
            <label className="block text-xs text-white mb-1">
              Temperature: {temperature}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
          
          <Button
            onClick={handleTest}
            disabled={testMutation.isPending || !prompt.trim()}
            className="w-full"
          >
            {testMutation.isPending ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Testing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Test Prompt
              </>
            )}
          </Button>
          
          {/* Test Results */}
          {testResult && (
            <div className="glass rounded-lg p-4 border border-white/10 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-200">Result</h3>
                <button
                  onClick={() => handleExportToWorkflow(prompt)}
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  <ArrowRight className="w-3 h-3" />
                  Export to Workflow
                </button>
              </div>
              
              <div className="bg-slate-900/50 rounded p-3">
                <div className="text-sm text-slate-300 whitespace-pre-wrap">
                  {testResult.output}
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <div className="text-slate-400">Cost</div>
                  <div className="text-green-400 font-medium">
                    ${testResult.cost.toFixed(4)}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400">Latency</div>
                  <div className="text-slate-200 font-medium">
                    {testResult.latency_ms}ms
                  </div>
                </div>
                <div>
                  <div className="text-slate-400">Tokens</div>
                  <div className="text-slate-200 font-medium">
                    {testResult.tokens_used.total}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        )}
        
        {/* A/B Test Tab */}
        {activeTab === 'ab-test' && (
        <div className="space-y-4 min-w-0">
          <div className="grid grid-cols-2 gap-4 min-w-0">
            <div className="min-w-0">
              <label className="block text-xs text-white mb-1">Prompt A</label>
              <Textarea
                value={promptA}
                onChange={(e) => setPromptA(e.target.value)}
                placeholder="First prompt to test"
                rows={6}
              />
            </div>
            <div className="min-w-0">
              <label className="block text-xs text-white mb-1">Prompt B</label>
              <Textarea
                value={promptB}
                onChange={(e) => setPromptB(e.target.value)}
                placeholder="Second prompt to test"
                rows={6}
              />
            </div>
          </div>
          
          <div className="min-w-0">
            <label className="block text-xs text-white mb-1">Test Inputs (one per line)</label>
            <Textarea
              value={abTestInputs.join('\n')}
              onChange={(e) => setAbTestInputs(e.target.value.split('\n'))}
              placeholder="Enter test inputs, one per line"
              rows={3}
            />
          </div>
          
          <Button
            onClick={handleABTest}
            disabled={abTestMutation.isPending || !promptA.trim() || !promptB.trim()}
            className="w-full"
          >
            {abTestMutation.isPending ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Running A/B Test...
              </>
            ) : (
              <>
                <TrendingUp className="w-4 h-4 mr-2" />
                Run A/B Test
              </>
            )}
          </Button>
          
          {/* A/B Test Results */}
          {abTestResult && (
            <div className="glass rounded-lg p-4 border border-white/10 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-200">A/B Test Results</h3>
                {abTestResult.winner && (
                  <div className={cn(
                    'px-2 py-1 rounded text-xs font-medium',
                    abTestResult.winner === 'a' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'
                  )}>
                    Winner: Prompt {abTestResult.winner.toUpperCase()}
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="text-xs font-medium text-slate-300">Prompt A</div>
                  <div className="bg-slate-900/50 rounded p-2 text-sm text-slate-300">
                    {abTestResult.prompt_a_result.output}
                  </div>
                  <div className="text-xs text-slate-400">
                    Cost: ${abTestResult.prompt_a_result.cost.toFixed(4)} • 
                    Latency: {abTestResult.prompt_a_result.latency_ms}ms
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="text-xs font-medium text-slate-300">Prompt B</div>
                  <div className="bg-slate-900/50 rounded p-2 text-sm text-slate-300">
                    {abTestResult.prompt_b_result.output}
                  </div>
                  <div className="text-xs text-slate-400">
                    Cost: ${abTestResult.prompt_b_result.cost.toFixed(4)} • 
                    Latency: {abTestResult.prompt_b_result.latency_ms}ms
                  </div>
                </div>
              </div>
              
              <div className="pt-3 border-t border-white/10">
                <div className="text-xs text-slate-400">
                  Cost Savings: ${abTestResult.comparison_metrics.cost_savings.toFixed(4)} • 
                  Latency Diff: {abTestResult.comparison_metrics.latency_diff}ms
                </div>
              </div>
            </div>
          )}
        </div>
        )}
        
        {/* Versions Tab */}
        {activeTab === 'versions' && (
        <div className="space-y-3">
          {versions && versions.length > 0 ? (
            versions.map((version) => (
              <div key={version.version_id} className="glass rounded-lg p-3 border border-white/10">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="text-sm font-medium text-slate-200">
                      {version.model} • {version.provider}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {new Date(version.created_at).toLocaleString()}
                    </div>
                  </div>
                  <button
                    onClick={() => handleExportToWorkflow(version.prompt)}
                    className="text-xs text-blue-400 hover:text-blue-300"
                  >
                    Export
                  </button>
                </div>
                <div className="text-xs text-slate-300 bg-slate-900/50 rounded p-2 mb-2">
                  {version.prompt.substring(0, 200)}...
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-400">
                  <span>Avg Cost: ${version.average_cost.toFixed(4)}</span>
                  <span>Avg Latency: {version.average_latency_ms}ms</span>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-slate-400 text-sm py-8">
              No prompt versions yet. Test prompts to create versions.
            </div>
          )}
        </div>
        )}
      </div>
    </div>
  );
}

