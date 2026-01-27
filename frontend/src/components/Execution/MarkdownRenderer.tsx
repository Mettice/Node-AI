/**
 * Markdown Renderer - Clean Typography for Instant Insights
 *
 * Renders markdown content with beautiful typography similar to Claude/Perplexity.
 * Features:
 * - Headers with proper hierarchy
 * - Code blocks with syntax highlighting
 * - Lists (ordered and unordered)
 * - Tables
 * - Blockquotes
 * - Inline formatting (bold, italic, code)
 * - Links
 */

import { useMemo, useState } from 'react';
import { Copy, Check, ChevronDown, ChevronRight } from 'lucide-react';
import { cn } from '@/utils/cn';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  const elements = useMemo(() => parseMarkdown(content), [content]);

  return (
    <div className={cn("markdown-content space-y-4", className)}>
      {elements.map((element, idx) => (
        <MarkdownElement key={idx} element={element} />
      ))}
    </div>
  );
}

// Markdown element types
type MarkdownElementType =
  | { type: 'h1'; content: string }
  | { type: 'h2'; content: string }
  | { type: 'h3'; content: string }
  | { type: 'h4'; content: string }
  | { type: 'paragraph'; content: string }
  | { type: 'code'; content: string; language?: string }
  | { type: 'blockquote'; content: string }
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: string[] }
  | { type: 'hr' }
  | { type: 'table'; headers: string[]; rows: string[][] };

function parseMarkdown(text: string): MarkdownElementType[] {
  const elements: MarkdownElementType[] = [];
  const lines = text.split('\n');
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmedLine = line.trim();

    // Empty line
    if (!trimmedLine) {
      i++;
      continue;
    }

    // Horizontal rule
    if (trimmedLine.match(/^[-*_]{3,}$/)) {
      elements.push({ type: 'hr' });
      i++;
      continue;
    }

    // Code block
    if (trimmedLine.startsWith('```')) {
      const language = trimmedLine.slice(3).trim() || undefined;
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      elements.push({ type: 'code', content: codeLines.join('\n'), language });
      i++; // Skip closing ```
      continue;
    }

    // Headers
    const h4Match = trimmedLine.match(/^####\s+(.+)$/);
    if (h4Match) {
      elements.push({ type: 'h4', content: h4Match[1] });
      i++;
      continue;
    }

    const h3Match = trimmedLine.match(/^###\s+(.+)$/);
    if (h3Match) {
      elements.push({ type: 'h3', content: h3Match[1] });
      i++;
      continue;
    }

    const h2Match = trimmedLine.match(/^##\s+(.+)$/);
    if (h2Match) {
      elements.push({ type: 'h2', content: h2Match[1] });
      i++;
      continue;
    }

    const h1Match = trimmedLine.match(/^#\s+(.+)$/);
    if (h1Match) {
      elements.push({ type: 'h1', content: h1Match[1] });
      i++;
      continue;
    }

    // Blockquote
    if (trimmedLine.startsWith('>')) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        quoteLines.push(lines[i].trim().replace(/^>\s*/, ''));
        i++;
      }
      elements.push({ type: 'blockquote', content: quoteLines.join('\n') });
      continue;
    }

    // Unordered list
    if (trimmedLine.match(/^[-*]\s+/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].trim().match(/^[-*]\s+/)) {
        items.push(lines[i].trim().replace(/^[-*]\s+/, ''));
        i++;
      }
      elements.push({ type: 'ul', items });
      continue;
    }

    // Ordered list
    if (trimmedLine.match(/^\d+\.\s+/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].trim().match(/^\d+\.\s+/)) {
        items.push(lines[i].trim().replace(/^\d+\.\s+/, ''));
        i++;
      }
      elements.push({ type: 'ol', items });
      continue;
    }

    // Table
    if (trimmedLine.includes('|') && lines[i + 1]?.includes('---')) {
      const headers = trimmedLine.split('|').map(h => h.trim()).filter(Boolean);
      i += 2; // Skip header and separator
      const rows: string[][] = [];
      while (i < lines.length && lines[i].includes('|')) {
        const row = lines[i].split('|').map(c => c.trim()).filter(Boolean);
        rows.push(row);
        i++;
      }
      elements.push({ type: 'table', headers, rows });
      continue;
    }

    // Regular paragraph - collect consecutive lines
    const paragraphLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith('#') &&
      !lines[i].trim().startsWith('```') &&
      !lines[i].trim().startsWith('>') &&
      !lines[i].trim().match(/^[-*]\s+/) &&
      !lines[i].trim().match(/^\d+\.\s+/) &&
      !lines[i].trim().match(/^[-*_]{3,}$/)
    ) {
      paragraphLines.push(lines[i].trim());
      i++;
    }
    if (paragraphLines.length > 0) {
      elements.push({ type: 'paragraph', content: paragraphLines.join(' ') });
    }
  }

  return elements;
}

function MarkdownElement({ element }: { element: MarkdownElementType }) {
  switch (element.type) {
    case 'h1':
      return (
        <h1 className="text-3xl font-bold text-white mb-6 mt-8 first:mt-0 pb-3 border-b border-white/10">
          <InlineContent content={element.content} />
        </h1>
      );

    case 'h2':
      return (
        <h2 className="text-2xl font-semibold text-blue-300 mb-4 mt-8 first:mt-0">
          <InlineContent content={element.content} />
        </h2>
      );

    case 'h3':
      return (
        <h3 className="text-xl font-semibold text-blue-200 mb-3 mt-6 first:mt-0">
          <InlineContent content={element.content} />
        </h3>
      );

    case 'h4':
      return (
        <h4 className="text-lg font-medium text-slate-200 mb-2 mt-4 first:mt-0">
          <InlineContent content={element.content} />
        </h4>
      );

    case 'paragraph':
      return (
        <p className="text-slate-300 leading-relaxed text-base">
          <InlineContent content={element.content} />
        </p>
      );

    case 'code':
      return <CodeBlock content={element.content} language={element.language} />;

    case 'blockquote':
      return (
        <blockquote className="border-l-4 border-blue-500/50 pl-4 py-2 my-4 bg-blue-500/5 rounded-r-lg">
          <p className="text-slate-300 italic">
            <InlineContent content={element.content} />
          </p>
        </blockquote>
      );

    case 'ul':
      return (
        <ul className="space-y-2 my-4">
          {element.items.map((item, idx) => (
            <li key={idx} className="flex items-start gap-3 text-slate-300">
              <span className="text-blue-400 mt-1.5 text-xs">●</span>
              <span className="flex-1">
                <InlineContent content={item} />
              </span>
            </li>
          ))}
        </ul>
      );

    case 'ol':
      return (
        <ol className="space-y-2 my-4">
          {element.items.map((item, idx) => (
            <li key={idx} className="flex items-start gap-3 text-slate-300">
              <span className="text-blue-400 font-medium min-w-[24px]">{idx + 1}.</span>
              <span className="flex-1">
                <InlineContent content={item} />
              </span>
            </li>
          ))}
        </ol>
      );

    case 'hr':
      return <hr className="border-white/10 my-8" />;

    case 'table':
      return (
        <div className="my-4 overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-white/20">
                {element.headers.map((header, idx) => (
                  <th key={idx} className="text-left py-3 px-4 text-slate-300 font-semibold bg-white/5">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {element.rows.map((row, rowIdx) => (
                <tr key={rowIdx} className="border-b border-white/10 hover:bg-white/5">
                  {row.map((cell, cellIdx) => (
                    <td key={cellIdx} className="py-3 px-4 text-slate-400">
                      <InlineContent content={cell} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );

    default:
      return null;
  }
}

// Code block with copy functionality
function CodeBlock({ content, language }: { content: string; language?: string }) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  const copyCode = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lineCount = content.split('\n').length;
  const isLong = lineCount > 15;

  return (
    <div className="my-4 rounded-xl overflow-hidden border border-white/10 bg-[#0d0d12]">
      <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10">
        <div className="flex items-center gap-2">
          {language && (
            <span className="text-xs text-slate-400 font-mono">{language}</span>
          )}
          {isLong && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300"
            >
              {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              {lineCount} lines
            </button>
          )}
        </div>
        <button
          onClick={copyCode}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-green-400" />
              Copied
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              Copy
            </>
          )}
        </button>
      </div>
      <div className={cn(
        "overflow-auto transition-all",
        isLong && !isExpanded && "max-h-48"
      )}>
        <pre className="p-4 text-sm">
          <code className="text-slate-300 font-mono whitespace-pre-wrap break-words">
            {content}
          </code>
        </pre>
      </div>
      {isLong && !isExpanded && (
        <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-[#0d0d12] to-transparent pointer-events-none" />
      )}
    </div>
  );
}

// Inline content parser for bold, italic, code, links
function InlineContent({ content }: { content: string }) {
  // Parse inline elements
  const parts = parseInline(content);

  return (
    <>
      {parts.map((part, idx) => {
        if (part.type === 'text') {
          return <span key={idx}>{part.content}</span>;
        }
        if (part.type === 'bold') {
          return <strong key={idx} className="font-semibold text-white">{part.content}</strong>;
        }
        if (part.type === 'italic') {
          return <em key={idx} className="italic text-slate-200">{part.content}</em>;
        }
        if (part.type === 'code') {
          return (
            <code key={idx} className="px-1.5 py-0.5 bg-white/10 rounded text-sm font-mono text-blue-300">
              {part.content}
            </code>
          );
        }
        if (part.type === 'link') {
          return (
            <a
              key={idx}
              href={part.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 underline underline-offset-2"
            >
              {part.content}
            </a>
          );
        }
        return null;
      })}
    </>
  );
}

type InlinePart =
  | { type: 'text'; content: string }
  | { type: 'bold'; content: string }
  | { type: 'italic'; content: string }
  | { type: 'code'; content: string }
  | { type: 'link'; content: string; url: string };

function parseInline(text: string): InlinePart[] {
  const parts: InlinePart[] = [];
  let remaining = text;

  const patterns = [
    { regex: /\*\*(.+?)\*\*/g, type: 'bold' as const },
    { regex: /__(.+?)__/g, type: 'bold' as const },
    { regex: /\*(.+?)\*/g, type: 'italic' as const },
    { regex: /_(.+?)_/g, type: 'italic' as const },
    { regex: /`([^`]+)`/g, type: 'code' as const },
    { regex: /\[([^\]]+)\]\(([^)]+)\)/g, type: 'link' as const },
  ];

  // Simple inline parsing - could be enhanced with proper tokenization
  let match;
  let lastIndex = 0;

  // Combined regex for all patterns
  const combinedRegex = /(\*\*(.+?)\*\*|__(.+?)__|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\)|\*([^*]+)\*|_([^_]+)_)/g;

  while ((match = combinedRegex.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text.slice(lastIndex, match.index) });
    }

    const fullMatch = match[0];

    if (fullMatch.startsWith('**') || fullMatch.startsWith('__')) {
      parts.push({ type: 'bold', content: match[2] || match[3] });
    } else if (fullMatch.startsWith('`')) {
      parts.push({ type: 'code', content: match[4] });
    } else if (fullMatch.startsWith('[')) {
      parts.push({ type: 'link', content: match[5], url: match[6] });
    } else if (fullMatch.startsWith('*') || fullMatch.startsWith('_')) {
      parts.push({ type: 'italic', content: match[7] || match[8] });
    }

    lastIndex = match.index + fullMatch.length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push({ type: 'text', content: text.slice(lastIndex) });
  }

  // If no patterns matched, return entire text
  if (parts.length === 0) {
    parts.push({ type: 'text', content: text });
  }

  return parts;
}

export default MarkdownRenderer;
