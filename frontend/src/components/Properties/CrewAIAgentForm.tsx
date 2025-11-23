/**
 * Custom form for CrewAI Agent configuration
 * Provides a user-friendly interface for configuring agents and tasks
 */

import { useState, useEffect, useRef } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Input } from '@/components/common/Input';
import { Textarea } from '@/components/common/Textarea';
import { Select } from '@/components/common/Select';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import { ProviderSelector } from './ProviderSelector';
import { APIKeyInputWithVault } from './APIKeyInputWithVault';
import { testLLMConnection } from '@/services/nodes';

interface Agent {
  name?: string;
  role: string;
  goal: string;
  backstory: string;
  tools?: any[];
}

interface Task {
  description: string;
  agent: string;
  expected_output?: string;
}

interface CrewAIAgentFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  schema?: Record<string, any>; // Schema to get model enums from
}

export function CrewAIAgentForm({ initialData, onChange, schema }: CrewAIAgentFormProps) {
  // Parse agents and tasks from initialData
  const parseAgents = (): Agent[] => {
    if (!initialData.agents) return [{ role: '', goal: '', backstory: '' }];
    if (typeof initialData.agents === 'string') {
      try {
        return JSON.parse(initialData.agents);
      } catch {
        return [{ role: '', goal: '', backstory: '' }];
      }
    }
    return Array.isArray(initialData.agents) ? initialData.agents : [{ role: '', goal: '', backstory: '' }];
  };

  const parseTasks = (): Task[] => {
    if (!initialData.tasks) return [{ description: '', agent: '', expected_output: '' }];
    if (typeof initialData.tasks === 'string') {
      try {
        return JSON.parse(initialData.tasks);
      } catch {
        return [{ description: '', agent: '', expected_output: '' }];
      }
    }
    return Array.isArray(initialData.tasks) ? initialData.tasks : [{ description: '', agent: '', expected_output: '' }];
  };

  const [provider, setProvider] = useState(initialData.provider || 'openai');
  
  // Get model lists from schema if available, otherwise use defaults
  const properties = schema?.properties || {};
  const openaiModels = properties.openai_model?.enum || [];
  const anthropicModels = properties.anthropic_model?.enum || [];
  const geminiModels = properties.gemini_model?.enum || [];
  
  // Get default models from schema or use fallbacks
  const defaultOpenaiModel = properties.openai_model?.default || 'gpt-4o-mini';
  const defaultAnthropicModel = properties.anthropic_model?.default || 'claude-sonnet-4-5-20250929';
  const defaultGeminiModel = properties.gemini_model?.default || 'gemini-2.5-flash';
  
  const [openaiModel, setOpenaiModel] = useState(initialData.openai_model || defaultOpenaiModel);
  const [anthropicModel, setAnthropicModel] = useState(initialData.anthropic_model || defaultAnthropicModel);
  const [geminiModel, setGeminiModel] = useState(initialData.gemini_model || defaultGeminiModel);
  const [openaiApiKey, setOpenaiApiKey] = useState(initialData.openai_api_key || '');
  const [anthropicApiKey, setAnthropicApiKey] = useState(initialData.anthropic_api_key || '');
  const [geminiApiKey, setGeminiApiKey] = useState(initialData.gemini_api_key || '');
  const [azureOpenaiApiKey, setAzureOpenaiApiKey] = useState(initialData.azure_openai_api_key || '');
  const [azureOpenaiEndpoint, setAzureOpenaiEndpoint] = useState(initialData.azure_openai_endpoint || '');
  const [azureOpenaiDeployment, setAzureOpenaiDeployment] = useState(initialData.azure_openai_deployment || '');
  
  // Track secret IDs for vault integration
  const [openaiSecretId, setOpenaiSecretId] = useState(initialData.openai_api_key_secret_id || '');
  const [anthropicSecretId, setAnthropicSecretId] = useState(initialData.anthropic_api_key_secret_id || '');
  const [geminiSecretId, setGeminiSecretId] = useState(initialData.gemini_api_key_secret_id || '');
  const [azureOpenaiSecretId, setAzureOpenaiSecretId] = useState(initialData.azure_openai_api_key_secret_id || '');
  
  // Update model when provider changes to ensure we have a valid model for the new provider
  useEffect(() => {
    if (provider === 'openai' && openaiModels.length > 0 && !openaiModels.includes(openaiModel)) {
      setOpenaiModel(defaultOpenaiModel);
    } else if (provider === 'anthropic' && anthropicModels.length > 0 && !anthropicModels.includes(anthropicModel)) {
      setAnthropicModel(defaultAnthropicModel);
    } else if ((provider === 'gemini' || provider === 'google') && geminiModels.length > 0 && !geminiModels.includes(geminiModel)) {
      setGeminiModel(defaultGeminiModel);
    } else if ((provider === 'azure_openai' || provider === 'azure') && !azureOpenaiDeployment) {
      // Azure OpenAI uses deployment name, not model selection
      // Just ensure we have the required fields
    }
  }, [provider, openaiModels, anthropicModels, geminiModels, azureOpenaiDeployment]);
  const [temperature, setTemperature] = useState(initialData.temperature ?? 0.7);
  const [maxIterations, setMaxIterations] = useState(initialData.max_iterations ?? 3);
  const [process, setProcess] = useState(initialData.process || 'sequential');
  const [agents, setAgents] = useState<Agent[]>(parseAgents);
  const [tasks, setTasks] = useState<Task[]>(parseTasks);
  const [taskDescription, setTaskDescription] = useState(initialData.task || '');
  const onChangeRef = useRef(onChange);

  // Keep onChange ref up to date
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  // Update parent when form changes (debounced to prevent infinite loops)
  useEffect(() => {
    // Get available agent roles for task assignment (calculate inside useEffect to avoid dependency issues)
    const agentRoles = agents
      .map((a) => a.role)
      .filter((role) => role.trim() !== '');

    const config: Record<string, any> = {
      provider,
      temperature,
      max_iterations: maxIterations,
      process,
    };

    if (provider === 'openai') {
      config.openai_model = openaiModel;
      if (openaiApiKey) {
        config.openai_api_key = openaiApiKey;
        if (openaiSecretId) {
          config.openai_api_key_secret_id = openaiSecretId;
        }
      }
    } else if (provider === 'azure_openai' || provider === 'azure') {
      if (azureOpenaiApiKey) {
        config.azure_openai_api_key = azureOpenaiApiKey;
        if (azureOpenaiSecretId) {
          config.azure_openai_api_key_secret_id = azureOpenaiSecretId;
        }
      }
      if (azureOpenaiEndpoint) {
        config.azure_openai_endpoint = azureOpenaiEndpoint;
      }
      if (azureOpenaiDeployment) {
        config.azure_openai_deployment = azureOpenaiDeployment;
      }
    } else if (provider === 'anthropic') {
      config.anthropic_model = anthropicModel;
      if (anthropicApiKey) {
        config.anthropic_api_key = anthropicApiKey;
        if (anthropicSecretId) {
          config.anthropic_api_key_secret_id = anthropicSecretId;
        }
      }
    } else if (provider === 'gemini' || provider === 'google') {
      config.gemini_model = geminiModel;
      if (geminiApiKey) {
        config.gemini_api_key = geminiApiKey;
        if (geminiSecretId) {
          config.gemini_api_key_secret_id = geminiSecretId;
        }
      }
    }

    if (taskDescription) {
      config.task = taskDescription;
    }

    // Only include agents if at least one has a role
    const validAgents = agents.filter((a) => a.role.trim() !== '');
    if (validAgents.length > 0) {
      config.agents = validAgents.map((a) => ({
        role: a.role,
        goal: a.goal || '',
        backstory: a.backstory || '',
      }));
    }

    // Only include tasks if at least one has a description
    const validTasks = tasks.filter((t) => t.description.trim() !== '');
    if (validTasks.length > 0) {
      config.tasks = validTasks.map((t) => ({
        description: t.description,
        agent: t.agent || (agentRoles[0] || ''),
        expected_output: t.expected_output || 'Complete the task successfully',
      }));
    }

    // Use ref to avoid dependency on onChange
    const timeoutId = setTimeout(() => {
      onChangeRef.current(config);
    }, 100); // Small debounce to prevent rapid updates

    return () => clearTimeout(timeoutId);
  }, [provider, openaiModel, anthropicModel, geminiModel, openaiApiKey, anthropicApiKey, geminiApiKey, azureOpenaiApiKey, azureOpenaiEndpoint, azureOpenaiDeployment, openaiSecretId, anthropicSecretId, geminiSecretId, azureOpenaiSecretId, temperature, maxIterations, process, agents, tasks, taskDescription]);

  const addAgent = () => {
    setAgents([...agents, { role: '', goal: '', backstory: '' }]);
  };

  const removeAgent = (index: number) => {
    setAgents(agents.filter((_, i) => i !== index));
  };

  const updateAgent = (index: number, field: keyof Agent, value: string) => {
    const updated = [...agents];
    updated[index] = { ...updated[index], [field]: value };
    setAgents(updated);
  };

  const addTask = () => {
    setTasks([...tasks, { description: '', agent: agentRoles[0] || '', expected_output: '' }]);
  };

  const removeTask = (index: number) => {
    setTasks(tasks.filter((_, i) => i !== index));
  };

  const updateTask = (index: number, field: keyof Task, value: string) => {
    const updated = [...tasks];
    updated[index] = { ...updated[index], [field]: value };
    setTasks(updated);
  };

  // Get available agent roles for task assignment (for UI display)
  const agentRoles = agents
    .map((a) => a.role)
    .filter((role) => role.trim() !== '');

  return (
    <div className="space-y-6">
      {/* Provider Selection */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">LLM Provider</label>
        <ProviderSelector
          currentProvider={provider}
          onChange={(value) => setProvider(value)}
          nodeType="crewai_agent"
        />
      </div>

      {/* Model Selection */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">
          {provider === 'openai' 
            ? 'OpenAI Model' 
            : provider === 'anthropic' 
            ? 'Anthropic Model' 
            : 'Gemini Model'}
        </label>
        {(provider === 'azure_openai' || provider === 'azure') ? (
          <div>
            <p className="text-sm text-slate-400">
              Azure OpenAI uses deployment names instead of model selection. 
              Enter your deployment name in the configuration below.
            </p>
          </div>
        ) : (
          <SelectWithIcons
            value={
              provider === 'openai' 
                ? openaiModel 
                : provider === 'anthropic' 
                ? anthropicModel 
                : geminiModel
            }
            onChange={(value) => {
              if (provider === 'openai') {
                setOpenaiModel(value);
              } else if (provider === 'anthropic') {
                setAnthropicModel(value);
              } else {
                setGeminiModel(value);
              }
            }}
            options={
              provider === 'openai'
                ? (openaiModels.length > 0
                    ? openaiModels.map((model: string) => ({
                        value: model,
                        label: model
                          .replace(/^gpt-/, 'GPT-')
                          .replace(/^o1-/, 'O1-')
                          .replace(/-/g, ' ')
                          .replace(/\b\w/g, (l) => l.toUpperCase()),
                        icon: 'openai',
                      }))
                    : [
                        { value: 'gpt-4', label: 'GPT-4', icon: 'openai' },
                        { value: 'gpt-4-turbo-preview', label: 'GPT-4 Turbo', icon: 'openai' },
                        { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', icon: 'openai' },
                      ])
                : provider === 'anthropic'
                ? (anthropicModels.length > 0
                    ? anthropicModels.map((model: string) => ({
                        value: model,
                        label: model
                          .replace(/^claude-/, 'Claude ')
                          .replace(/-/g, ' ')
                          .replace(/\b\w/g, (l) => l.toUpperCase()),
                        icon: 'anthropic',
                      }))
                    : [
                        { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus', icon: 'anthropic' },
                        { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet', icon: 'anthropic' },
                        { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku', icon: 'anthropic' },
                      ])
                : (geminiModels.length > 0
                    ? geminiModels.map((model: string) => ({
                        value: model,
                        label: model
                          .replace(/^gemini-/, 'Gemini ')
                          .replace(/-/g, ' ')
                          .replace(/\b\w/g, (l) => l.toUpperCase()),
                        icon: 'gemini',
                      }))
                    : [
                        { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro', icon: 'gemini' },
                        { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash', icon: 'gemini' },
                      ])
            }
          />
        )}
      </div>

      {/* API Key Input (only show for selected provider) - Using Vault Integration */}
      {provider === 'openai' && (
        <APIKeyInputWithVault
          value={openaiApiKey}
          onChange={(value, secretId) => {
            setOpenaiApiKey(value);
            setOpenaiSecretId(secretId || '');
          }}
          placeholder="Enter OpenAI API key (optional, uses environment variable if not provided)..."
          label="OpenAI API Key"
          description="Optional: Provide your OpenAI API key here. If not provided, the system will use the OPENAI_API_KEY environment variable."
          serviceName="OpenAI"
          provider="openai"
          testConnection={async (apiKey: string) => {
            return await testLLMConnection('openai', apiKey);
          }}
        />
      )}
      {provider === 'anthropic' && (
        <APIKeyInputWithVault
          value={anthropicApiKey}
          onChange={(value, secretId) => {
            setAnthropicApiKey(value);
            setAnthropicSecretId(secretId || '');
          }}
          placeholder="Enter Anthropic API key (optional, uses environment variable if not provided)..."
          label="Anthropic API Key"
          description="Optional: Provide your Anthropic API key here. If not provided, the system will use the ANTHROPIC_API_KEY environment variable."
          serviceName="Anthropic"
          provider="anthropic"
          testConnection={async (apiKey: string) => {
            return await testLLMConnection('anthropic', apiKey);
          }}
        />
      )}
      {(provider === 'gemini' || provider === 'google') && (
        <APIKeyInputWithVault
          value={geminiApiKey}
          onChange={(value, secretId) => {
            setGeminiApiKey(value);
            setGeminiSecretId(secretId || '');
          }}
          placeholder="Enter Gemini API key (optional, uses environment variable if not provided)..."
          label="Gemini API Key"
          description="Optional: Provide your Google Gemini API key here. If not provided, the system will use the GEMINI_API_KEY environment variable."
          serviceName="Google Gemini"
          provider="google"
          testConnection={async (apiKey: string) => {
            return await testLLMConnection('gemini', apiKey);
          }}
        />
      )}
      {(provider === 'azure_openai' || provider === 'azure') && (
        <div className="space-y-4">
          <APIKeyInputWithVault
            value={azureOpenaiApiKey}
            onChange={(value, secretId) => {
              setAzureOpenaiApiKey(value);
              setAzureOpenaiSecretId(secretId || '');
            }}
            placeholder="Enter Azure OpenAI API key..."
            label="Azure OpenAI API Key"
            description="Azure OpenAI API key (required)"
            serviceName="Azure OpenAI"
            provider="azure_openai"
            testConnection={async (_apiKey: string) => {
              // Azure OpenAI connection test would require endpoint and deployment
              // For now, just return true - full validation would need all three parameters
              return true;
            }}
          />
          <div>
            <label className="block text-sm font-medium text-white mb-2">Azure OpenAI Endpoint</label>
            <input
              type="text"
              value={azureOpenaiEndpoint}
              onChange={(e) => setAzureOpenaiEndpoint(e.target.value)}
              placeholder="https://your-resource.openai.azure.com"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <p className="text-xs text-slate-400 mt-1">Azure OpenAI endpoint URL</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">Deployment Name</label>
            <input
              type="text"
              value={azureOpenaiDeployment}
              onChange={(e) => setAzureOpenaiDeployment(e.target.value)}
              placeholder="gpt-4, gpt-35-turbo, etc."
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <p className="text-xs text-slate-400 mt-1">Azure OpenAI deployment name</p>
          </div>
        </div>
      )}

      {/* Temperature */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">
          Temperature ({temperature})
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

      {/* Max Iterations */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">Max Iterations</label>
        <Input
          type="number"
          min="1"
          max="10"
          value={maxIterations}
          onChange={(e) => setMaxIterations(parseInt(e.target.value, 10))}
        />
      </div>

      {/* Process Type */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">Process Type</label>
        <Select
          value={process}
          onChange={(e) => setProcess(e.target.value)}
          options={[
            { value: 'sequential', label: 'Sequential (one after another)' },
            { value: 'hierarchical', label: 'Hierarchical (parallel with coordination)' },
          ]}
        />
      </div>

      {/* Main Task Description (Optional - can be used instead of tasks array) */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">
          Main Task Description (Optional)
        </label>
        <Textarea
          value={taskDescription}
          onChange={(e) => setTaskDescription(e.target.value)}
          placeholder="Enter the main task for the crew..."
          rows={3}
        />
        <p className="text-xs text-slate-400 mt-1">
          If provided, this will be used as a default task if no tasks are defined below.
        </p>
      </div>

      {/* Agents Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-white">Agents</label>
          <button
            type="button"
            onClick={addAgent}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-purple-600 hover:bg-purple-700 text-white rounded"
          >
            <Plus className="w-3 h-3" />
            Add Agent
          </button>
        </div>

        <div className="space-y-4">
          {agents.map((agent, index) => (
            <div key={index} className="p-4 bg-white/5 rounded-lg border border-white/10">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-white">Agent {index + 1}</span>
                {agents.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeAgent(index)}
                    className="text-red-400 hover:text-red-300"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Role *</label>
                  <Input
                    value={agent.role}
                    onChange={(e) => updateAgent(index, 'role', e.target.value)}
                    placeholder="e.g., Researcher, Writer, Analyst"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 mb-1">Goal *</label>
                  <Textarea
                    value={agent.goal}
                    onChange={(e) => updateAgent(index, 'goal', e.target.value)}
                    placeholder="What is this agent trying to achieve?"
                    rows={2}
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 mb-1">Backstory</label>
                  <Textarea
                    value={agent.backstory}
                    onChange={(e) => updateAgent(index, 'backstory', e.target.value)}
                    placeholder="Agent's expertise, background, and personality"
                    rows={2}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tasks Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-white">Tasks</label>
          <button
            type="button"
            onClick={addTask}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-purple-600 hover:bg-purple-700 text-white rounded"
          >
            <Plus className="w-3 h-3" />
            Add Task
          </button>
        </div>

        <div className="space-y-4">
          {tasks.map((task, index) => (
            <div key={index} className="p-4 bg-white/5 rounded-lg border border-white/10">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-white">Task {index + 1}</span>
                {tasks.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeTask(index)}
                    className="text-red-400 hover:text-red-300"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Description *</label>
                  <Textarea
                    value={task.description}
                    onChange={(e) => updateTask(index, 'description', e.target.value)}
                    placeholder="What needs to be done?"
                    rows={2}
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 mb-1">Assigned Agent</label>
                  <Select
                    value={task.agent}
                    onChange={(e) => updateTask(index, 'agent', e.target.value)}
                    options={[
                      { value: '', label: 'Select agent...' },
                      ...agentRoles.map((role) => ({ value: role, label: role })),
                    ]}
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 mb-1">Expected Output</label>
                  <Textarea
                    value={task.expected_output || ''}
                    onChange={(e) => updateTask(index, 'expected_output', e.target.value)}
                    placeholder="What should this task produce? (e.g., 'A comprehensive research report')"
                    rows={2}
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    Optional. Defaults to "Complete the task successfully" if not provided.
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Info Box */}
      <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
        <p className="text-xs text-blue-300">
          <strong>💡 Tip:</strong> Connect Tool nodes to provide capabilities to agents. Agents can use tools
          from connected nodes automatically.
        </p>
      </div>
    </div>
  );
}

