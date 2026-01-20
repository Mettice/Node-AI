/**
 * Provider Icon Component
 * Displays colorful icons for different providers/services using Simple Icons
 */

import { cn } from '@/utils/cn';
import { 
  Database, 
  Cloud, 
  Search, 
  Zap, 
  Brain,
  Layers,
  Box,
  Calculator,
  Code,
  Wrench,
  Mail,
  Globe,
  Rss,
  FileSpreadsheet
} from 'lucide-react';

// Import Simple Icons - icons are exported as si{Name} (e.g., siOpenai, siAnthropic)
import * as simpleIcons from 'simple-icons';

interface ProviderIconProps {
  provider: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

// Map provider names to Simple Icons export names (si{Name} format)
// Only includes icons that exist in simple-icons package
// Missing icons will use fallback (first letter)
const PROVIDER_ICON_MAP: Record<string, string> = {
  // LLM Providers
  openai: 'siOpenai',
  anthropic: 'siAnthropic',
  gemini: 'siGooglegemini',
  
  // Embedding Providers
  huggingface: 'siHuggingface',
  // cohere: not available in simple-icons
  // voyage_ai: not available in simple-icons
  
  // Vector Stores
  faiss: 'siFacebook', // FAISS is from Facebook, use their icon
  // pinecone: not available in simple-icons
  gemini_file_search: 'siGooglegemini',
  // qdrant: not available in simple-icons
  
  // Integrations (only those available in simple-icons)
  // s3: not available in simple-icons (no AWS S3 specific icon)
  postgresql: 'siPostgresql',
  reddit: 'siReddit',
  salesforce: 'siSalesforce',
  // sharepoint: not available in simple-icons
  perplexity: 'siPerplexity',
  // pipedrive: not available in simple-icons
  resend: 'siResend',
  // serper: not available in simple-icons
  slack: 'siSlack',
  notion: 'siNotion',
  airtable: 'siAirtable',
  googledrive: 'siGoogledrive',
  
  // Databases
  sqlite: 'siSqlite',
  mysql: 'siMysql',
  
  // Programming Languages
  python: 'siPython',
  javascript: 'siJavascript',
  
  // Agent Frameworks
  crewai: 'siCrewai',
  langchain: 'siLangchain',
};

// Tool type icons (using Lucide icons)
const TOOL_TYPE_ICONS: Record<string, { icon: React.ComponentType<{ className?: string }>, color: string }> = {
  calculator: { icon: Calculator, color: '#8B5CF6' }, // Purple
  search: { icon: Search, color: '#3B82F6' }, // Blue
  web_scraping: { icon: Globe, color: '#06B6D4' }, // Cyan
  rss_feed: { icon: Rss, color: '#F97316' }, // Orange
  s3: { icon: Cloud, color: '#FF9900' }, // AWS Orange
  code: { icon: Code, color: '#10B981' }, // Green
  database: { icon: Database, color: '#F59E0B' }, // Amber
  api: { icon: Cloud, color: '#EF4444' }, // Red
  email: { icon: Mail, color: '#EC4899' }, // Pink
  wrench: { icon: Wrench, color: '#6B7280' }, // Gray
};

// Fallback icons for providers without simple-icons
// Maps provider to { icon component, color }
const FALLBACK_ICONS: Record<string, { icon: React.ComponentType<{ className?: string }>, color: string }> = {
  // Embedding Providers
  cohere: { icon: Brain, color: '#FF6D3A' }, // Cohere brand color
  voyage_ai: { icon: Zap, color: '#6366F1' }, // Voyage AI brand color
  
  // Vector Stores
  pinecone: { icon: Database, color: '#5A67D8' }, // Pinecone brand color
  qdrant: { icon: Layers, color: '#9333EA' }, // Qdrant brand color
  
  // Integrations
  s3: { icon: Cloud, color: '#FF9900' }, // AWS brand color
  sharepoint: { icon: Box, color: '#0078D4' }, // Microsoft brand color
  pipedrive: { icon: Database, color: '#1A9F85' }, // Pipedrive brand color
  serper: { icon: Search, color: '#1E40AF' }, // Serper brand color
  serpapi: { icon: Search, color: '#4285F4' }, // SerpAPI brand color (similar to Google)
  duckduckgo: { icon: Search, color: '#DE5833' }, // DuckDuckGo brand color
  brave: { icon: Search, color: '#FB542B' }, // Brave Search brand color
  perplexity: { icon: Brain, color: '#8B5CF6' }, // Perplexity brand color (purple, AI-powered)
  
  // Databases (fallback if not in simple-icons)
  sqlite: { icon: Database, color: '#003B57' }, // SQLite brand color
  mysql: { icon: Database, color: '#4479A1' }, // MySQL brand color
};

const SIZE_CLASSES = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
};

export function ProviderIcon({ provider, size = 'md', className }: ProviderIconProps) {
  // First check if it's a tool type icon
  const toolTypeIcon = TOOL_TYPE_ICONS[provider.toLowerCase()];
  if (toolTypeIcon) {
    const ToolIcon = toolTypeIcon.icon;
    return (
      <div
        className={cn(
          'rounded flex items-center justify-center',
          SIZE_CLASSES[size],
          className
        )}
        style={{ backgroundColor: toolTypeIcon.color }}
        title={provider}
      >
        <ToolIcon className="w-full h-full p-0.5 text-white" />
      </div>
    );
  }
  
  // Normalize provider names for icon lookup
  let normalizedProvider = provider.toLowerCase();
  if (normalizedProvider === 'google') {
    normalizedProvider = 'gemini'; // For LLM/embedding providers
  } else if (normalizedProvider === 'google_drive') {
    normalizedProvider = 'googledrive'; // For Google Drive node
  } else if (normalizedProvider === 'googlesheets') {
    // Google Sheets uses a special fallback icon (FileSpreadsheet with Google green)
    const GoogleSheetsIcon = FileSpreadsheet;
    return (
      <div
        className={cn(
          'rounded flex items-center justify-center',
          SIZE_CLASSES[size],
          className
        )}
        style={{ backgroundColor: '#0F9D58' }} // Google Sheets green
        title="Google Sheets"
      >
        <GoogleSheetsIcon className="w-full h-full p-0.5 text-white" />
      </div>
    );
  }
  const iconSlug = PROVIDER_ICON_MAP[normalizedProvider];
  
  // Try to get icon from Simple Icons
  let iconData: { path: string; hex: string; title: string } | null = null;
  
  if (iconSlug) {
    try {
      const icon = (simpleIcons as any)[iconSlug];
      if (icon && icon.path && icon.hex) {
        iconData = {
          path: icon.path,
          hex: `#${icon.hex}`,
          title: icon.title || provider,
        };
      }
    } catch (e) {
      // Icon not found, will use fallback
    }
  }
  
  if (!iconData) {
    // Check for fallback icon with brand color (use normalized provider)
    const fallback = FALLBACK_ICONS[normalizedProvider];
    
    if (fallback) {
      const FallbackIcon = fallback.icon;
      return (
        <div
          className={cn(
            'rounded flex items-center justify-center',
            SIZE_CLASSES[size],
            className
          )}
          style={{ backgroundColor: fallback.color }}
          title={provider}
        >
          <FallbackIcon className="w-full h-full p-0.5 text-white" />
        </div>
      );
    }
    
    // Final fallback: first letter
    return (
      <div
        className={cn(
          'rounded flex items-center justify-center bg-slate-600 text-white font-semibold text-xs',
          SIZE_CLASSES[size],
          className
        )}
        title={provider}
      >
        {provider.charAt(0).toUpperCase()}
      </div>
    );
  }

  return (
    <div
      className={cn(
        'rounded flex items-center justify-center',
        SIZE_CLASSES[size],
        className
      )}
      style={{ backgroundColor: iconData.hex }}
      title={iconData.title}
    >
      <svg
        role="img"
        viewBox="0 0 24 24"
        className="w-full h-full p-0.5"
        fill="white"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path d={iconData.path} />
      </svg>
    </div>
  );
}

// Export provider metadata for use in other components
export function getProviderInfo(provider: string) {
  // Normalize provider names for icon lookup
  let normalizedProvider = provider.toLowerCase();
  if (normalizedProvider === 'google') {
    normalizedProvider = 'gemini'; // For LLM/embedding providers
  } else if (normalizedProvider === 'google_drive') {
    normalizedProvider = 'googledrive'; // For Google Drive node
  } else if (normalizedProvider === 'googlesheets') {
    // Google Sheets uses special branding
    return {
      bg: '#0F9D58', // Google Sheets green
      icon: null, // Uses FileSpreadsheet Lucide icon
      name: 'Google Sheets',
    };
  }
  const iconSlug = PROVIDER_ICON_MAP[normalizedProvider];
  
  if (iconSlug) {
    try {
      const icon = (simpleIcons as any)[iconSlug];
      if (icon && icon.path && icon.hex) {
        return {
          bg: `#${icon.hex}`,
          icon: icon.path,
          name: icon.title || provider,
        };
      }
    } catch (e) {
      // Icon not found
    }
  }
  
  // Check for fallback icon (use normalized provider)
  const fallback = FALLBACK_ICONS[normalizedProvider];
  if (fallback) {
    return {
      bg: fallback.color,
      icon: 'lucide', // Indicates it's a Lucide icon
      name: provider,
    };
  }
  
  return {
    bg: '#64748b', // slate-600
    icon: provider.charAt(0).toUpperCase(),
    name: provider,
  };
}

