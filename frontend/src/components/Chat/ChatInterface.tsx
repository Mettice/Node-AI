/**
 * ChatInterface component - main chat panel with history and input
 */

import { useEffect, useRef } from 'react';
import { MessageSquare, Trash2, AlertCircle, CheckCircle2, X, BrainCircuit } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { useExecutionStore } from '@/store/executionStore';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { executeWorkflow } from '@/services/workflows';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';

interface ChatInterfaceProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChatInterface({ isOpen, onClose }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    messages,
    isProcessing,
    vectorStoreReady,
    memoryEnabled,
    sessionId,
    addMessage,
    clearMessages,
    setProcessing,
    setVectorStoreReady,
    setMemoryEnabled,
  } = useChatStore();
  
  const { nodes, edges } = useWorkflowStore();
  const { updateStatus, updateCost, updateDuration } = useExecutionStore();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check if workflow has necessary nodes for RAG
  const hasRequiredNodes = () => {
    const nodeTypes = nodes.map(n => n.type);
    const hasVectorStore = nodeTypes.includes('vector_store');
    const hasVectorSearch = nodeTypes.includes('vector_search');
    const hasChat = nodeTypes.includes('chat');
    return hasVectorStore && hasVectorSearch && hasChat;
  };

  // Handle sending a message/query
  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    // Check if workflow is ready
    if (!hasRequiredNodes()) {
      toast.error('Please build a workflow with Vector Store, Vector Search, and Chat nodes first.');
      return;
    }

    // Add user message
    addMessage({
      role: 'user',
      content: message,
    });

    try {
      setProcessing(true);
      updateStatus('running');

      // Find the vector_search and chat nodes
      const vectorSearchNode = nodes.find(n => n.type === 'vector_search');
      const chatNode = nodes.find(n => n.type === 'chat');
      
      if (!vectorSearchNode || !chatNode) {
        throw new Error('Missing required nodes');
      }

      // Find vector_store node to get index_id
      const vectorStoreNode = nodes.find(n => n.type === 'vector_store');
      
      // Get index_id from vector_store node's config or from previous execution results
      const { results } = useExecutionStore.getState();
      const vectorStoreResult = vectorStoreNode ? results[vectorStoreNode.id] : null;
      const indexId = vectorStoreNode?.data?.config?.index_id || 
                      vectorStoreNode?.data?.index_id ||
                      vectorStoreResult?.output?.index_id ||
                      vectorSearchNode.data?.config?.index_id ||
                      vectorSearchNode.data?.index_id;

      // Build workflow with query injected into vector search and chat nodes
      const workflowNodes = nodes.map((node) => {
        // Get base config (flattened like ExecutionControls does)
        const baseConfig = node.data?.config || node.data || {};
        
        // For vector search node, inject the query (for searching) and ensure index_id is set
        // For chat node, inject the query (for the prompt template)
        let config = baseConfig;
        if (node.id === vectorSearchNode.id) {
          config = { 
            ...baseConfig, 
            query: message,
            // Ensure index_id is set - critical for finding the stored vectors
            ...(indexId && !baseConfig.index_id ? { index_id: indexId } : {}),
          };
        } else if (node.id === chatNode.id) {
          config = { 
            ...baseConfig, 
            query: message,
            // Add memory settings if enabled
            use_memory: memoryEnabled,
            session_id: sessionId,
            memory_limit: 10, // Default to 10 past messages
          };
        }

        // Debug: Log node configs
        if (node.id === vectorSearchNode.id || node.id === chatNode.id) {
          console.log(`🔍 ${node.type} Node Config:`, {
            nodeId: node.id,
            originalConfig: baseConfig,
            injectedQuery: message,
            finalConfig: config,
            ...(node.id === vectorSearchNode.id && { indexId, vectorStoreNodeId: vectorStoreNode?.id }),
          });
        }

        return {
          id: node.id,
          type: node.type || '',
          position: node.position,
          data: config, // Backend expects config directly in data
        };
      });

      const workflowEdges = edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
      }));

      // Debug: Log the full workflow payload
      console.log('📤 Sending workflow to backend:', {
        name: vectorStoreReady ? 'Chat Query' : 'Chat Initialization',
        nodesCount: workflowNodes.length,
        edgesCount: workflowEdges.length,
        vectorSearchNode: workflowNodes.find(n => n.id === vectorSearchNode.id),
      });

      // Execute workflow
      const result = await executeWorkflow({
        name: vectorStoreReady ? 'Chat Query' : 'Chat Initialization',
        nodes: workflowNodes,
        edges: workflowEdges,
      });

      // If execution is still running, poll for completion
      let finalResult = result;
      if (result.status === 'running' || result.status === 'pending') {
        // Poll for completion (max 120 seconds = 60 polls at 2000ms interval)
        // Using 2 second interval to avoid rate limiting (30 requests/minute limit)
        const maxPolls = 60;
        let pollCount = 0;
        
        while ((finalResult.status === 'running' || finalResult.status === 'pending') && pollCount < maxPolls) {
          await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
          
          try {
            const { getExecutionStatus } = await import('@/services/executions');
            finalResult = await getExecutionStatus(result.execution_id);
            pollCount++;
          } catch (pollError) {
            console.error('Error polling execution status:', pollError);
            break;
          }
        }
        
        if (finalResult.status === 'running' || finalResult.status === 'pending') {
          throw new Error('Execution timed out');
        }
      }

      // Mark vector store as ready after first successful execution
      if (!vectorStoreReady && finalResult.status === 'completed') {
        setVectorStoreReady(true);
        toast.success('Knowledge base ready!');
      }

      if (finalResult.status === 'completed') {
        // Extract chat response from results
        const chatResult = finalResult.results?.[chatNode.id];
        const vectorSearchResult = finalResult.results?.[vectorSearchNode.id];
        
        console.log('Chat result:', chatResult);
        console.log('Chat node ID:', chatNode.id);
        console.log('All results:', finalResult.results);
        
               // Handle different response formats
               const responseText = chatResult?.output?.response || chatResult?.output?.content || (chatResult?.output as any)?.response;
        
        if (responseText) {
          addMessage({
            role: 'assistant',
            content: responseText,
            cost: finalResult.total_cost,
            sources: vectorSearchResult?.output?.results || [],
          });
          
          updateCost(finalResult.total_cost);
          updateDuration(finalResult.duration_ms);
          updateStatus('completed');
        } else {
          console.error('Chat result structure:', JSON.stringify(chatResult, null, 2));
          throw new Error(`No response from chat node. Got: ${JSON.stringify(chatResult?.output || chatResult)}`);
        }
      } else {
        throw new Error(finalResult.status === 'failed' ? 'Execution failed' : 'Execution incomplete');
      }
    } catch (error) {
      console.error('Chat error:', error);
      addMessage({
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
      toast.error('Failed to process your question');
      updateStatus('failed');
    } finally {
      setProcessing(false);
    }
  };

  const handleClear = () => {
    if (confirm('Clear all messages and reset the conversation?')) {
      clearMessages();
      toast.success('Conversation cleared');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end pointer-events-none">
      {/* Chat Panel */}
      <div className="pointer-events-auto w-full md:w-96 h-[600px] m-4 glass-strong rounded-xl shadow-2xl border border-white/20 flex flex-col">
        {/* Header */}
        <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-semibold text-white">Chat</h2>
            {vectorStoreReady && (
              <div title="Knowledge base ready">
                <CheckCircle2 className="w-4 h-4 text-green-400" />
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Memory Toggle */}
            <button
              onClick={() => setMemoryEnabled(!memoryEnabled)}
              className={cn(
                "p-1.5 rounded transition-colors relative",
                memoryEnabled
                  ? "bg-amber-500/20 hover:bg-amber-500/30 text-amber-400"
                  : "hover:bg-white/10 text-slate-400"
              )}
              title={memoryEnabled ? "Memory enabled - Click to disable" : "Memory disabled - Click to enable"}
            >
              <BrainCircuit className="w-4 h-4" />
              {memoryEnabled && (
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-amber-400 rounded-full" />
              )}
            </button>
            <button
              onClick={handleClear}
              disabled={messages.length === 0}
              className="p-1.5 rounded hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Clear conversation"
            >
              <Trash2 className="w-4 h-4 text-slate-400" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded hover:bg-white/10 transition-colors"
              title="Close chat"
            >
              <X className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8">
              <MessageSquare className="w-12 h-12 text-slate-600 mb-4" />
              <h3 className="text-lg font-semibold text-slate-300 mb-2">
                No messages yet
              </h3>
              <p className="text-sm text-slate-500 mb-4">
                {hasRequiredNodes()
                  ? vectorStoreReady
                    ? 'Ask a question to get started!'
                    : 'Your first question will initialize the knowledge base.'
                  : 'Build a workflow with Vector Store, Vector Search, and Chat nodes first.'}
              </p>
              {!hasRequiredNodes() && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-left">
                  <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-yellow-300">
                    <p className="font-semibold mb-1">Required Nodes:</p>
                    <ul className="list-disc list-inside text-xs space-y-0.5">
                      <li>Vector Store (to store documents)</li>
                      <li>Vector Search (to find relevant content)</li>
                      <li>Chat (to generate responses)</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {/* Thinking indicator when processing */}
              {isProcessing && (
                <div className="flex gap-3 p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 animate-pulse">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-amber-500/20">
                    <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-amber-400 mb-1">Thinking...</div>
                    <div className="text-xs text-slate-400 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="inline-block w-1.5 h-1.5 bg-amber-400 rounded-full animate-pulse" />
                        Searching knowledge base...
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="inline-block w-1.5 h-1.5 bg-slate-500 rounded-full" />
                        Generating response...
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-white/10">
          <ChatInput
            onSend={handleSendMessage}
            disabled={isProcessing || !hasRequiredNodes()}
            placeholder={
              !hasRequiredNodes()
                ? 'Build a workflow first...'
                : vectorStoreReady
                ? 'Ask a question...'
                : 'Your first question will initialize the knowledge base...'
            }
          />
        </div>
      </div>
    </div>
  );
}

