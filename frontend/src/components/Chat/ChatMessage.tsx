/**
 * ChatMessage component - displays individual user/assistant messages
 */

import { User, Bot, DollarSign } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { ChatMessage as ChatMessageType } from '@/store/chatStore';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  
  return (
    <div
      className={cn(
        'flex gap-3 p-4 rounded-lg',
        isUser
          ? 'bg-blue-500/10 border border-blue-500/20'
          : 'bg-purple-500/10 border border-purple-500/20'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser
            ? 'bg-blue-500/20 text-blue-400'
            : 'bg-purple-500/20 text-purple-400'
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-semibold text-slate-200">
            {isUser ? 'You' : 'Assistant'}
          </span>
          <span className="text-xs text-slate-500">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
          {message.cost !== undefined && message.cost > 0 && (
            <div className="flex items-center gap-1 text-xs text-blue-400">
              <DollarSign className="w-3 h-3" />
              {message.cost.toFixed(4)}
            </div>
          )}
        </div>
        
        <div className="text-sm text-slate-300 whitespace-pre-wrap break-words max-w-full">
          {message.content}
        </div>

        {/* Sources (if available) */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 space-y-2">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
              Sources ({message.sources.length})
            </div>
            {message.sources.map((source, idx) => (
              <details key={idx} className="text-xs p-2 rounded bg-white/5 border border-white/10 cursor-pointer group">
                <summary className="list-none flex items-center justify-between">
                  <span className="text-slate-400 flex items-center gap-1">
                    <span className="inline-block group-open:rotate-90 transition-transform">▶</span>
                    Source {idx + 1} (click to expand)
                  </span>
                  <span className="text-blue-400">
                    Score: {source.score.toFixed(3)}
                  </span>
                </summary>
                <div className="mt-2 pt-2 border-t border-white/10 text-slate-300 whitespace-pre-wrap">
                  {source.text}
                </div>
              </details>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

