/**
 * Airtable Read Node Form Component
 * Provides API key configuration and Airtable read settings
 */

import { useState, useEffect, useRef } from 'react';
import { FileSpreadsheet, Search, Filter } from 'lucide-react';
import { APIKeyInputWithVault } from './APIKeyInputWithVault';
import { testAirtableConnection } from '@/services/nodes';

interface AirtableNodeFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  schema?: Record<string, any>;
}

export function AirtableNodeForm({ initialData, onChange }: AirtableNodeFormProps) {
  const [operation, setOperation] = useState(initialData.operation || 'read');
  const [baseId, setBaseId] = useState(initialData.base_id || '');
  const [tableName, setTableName] = useState(initialData.table_name || '');
  const [apiKey, setApiKey] = useState(initialData.api_key || '');
  const [view, setView] = useState(initialData.view || '');
  const [filterByFormula, setFilterByFormula] = useState(initialData.filter_by_formula || '');
  const [maxRecords, setMaxRecords] = useState(initialData.max_records || '');
  
  const onChangeRef = useRef(onChange);
  
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    const config: Record<string, any> = {
      operation,
      base_id: baseId,
      table_name: tableName,
      api_key: apiKey,
    };

    if (operation === 'read') {
      if (view) config.view = view;
      if (filterByFormula) config.filter_by_formula = filterByFormula;
      if (maxRecords) config.max_records = parseInt(maxRecords) || undefined;
    }

    onChangeRef.current(config);
  }, [operation, baseId, tableName, apiKey, view, filterByFormula, maxRecords]);

  return (
    <div className="space-y-4">
      {/* API Key */}
      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          API Key <span className="text-red-400">*</span>
        </label>
        <p className="text-xs text-slate-400 -mt-1">
          Get your API key from{' '}
          <a 
            href="https://airtable.com/api" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-purple-400 hover:text-purple-300 underline"
          >
            airtable.com/api
          </a>
        </p>
        <APIKeyInputWithVault
          value={apiKey}
          onChange={setApiKey}
          provider="airtable"
          placeholder="key123abc..."
          serviceName="Airtable"
          testConnection={testAirtableConnection}
        />
      </div>

      {/* Operation Selector */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4" />
          Operation
        </h3>
        
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Operation Type
          </label>
          <select
            value={operation}
            onChange={(e) => setOperation(e.target.value)}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          >
            <option value="read">Read</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="upsert">Upsert</option>
          </select>
          {operation !== 'read' && (
            <p className="text-xs text-slate-400 mt-1">
              {operation === 'create' && 'Add new records'}
              {operation === 'update' && 'Update existing records (requires "id" field)'}
              {operation === 'upsert' && 'Create or update records'}
            </p>
          )}
        </div>
      </div>

      {/* Base and Table Configuration */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4" />
          Base & Table Configuration
        </h3>
        
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Base ID <span className="text-red-400">*</span>
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            From the Airtable URL: /app{'{baseId}'}/...
          </p>
          <input
            type="text"
            value={baseId}
            onChange={(e) => setBaseId(e.target.value)}
            placeholder="app123abc..."
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Table Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={tableName}
            onChange={(e) => setTableName(e.target.value)}
            placeholder="Users"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          />
        </div>
      </div>

      {/* Advanced Options (only for read) */}
      {operation === 'read' && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Filter className="w-4 h-4" />
            Advanced Options
          </h3>
        
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            View (Optional)
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            Name of the view to read from
          </p>
          <input
            type="text"
            value={view}
            onChange={(e) => setView(e.target.value)}
            placeholder="Grid View"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Filter Formula (Optional)
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            Airtable formula to filter records (e.g., {'{'}{'{Status}'} = 'Active'{'}'})
          </p>
          <input
            type="text"
            value={filterByFormula}
            onChange={(e) => setFilterByFormula(e.target.value)}
            placeholder="{Status} = 'Active'"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Max Records (Optional)
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            Maximum number of records to fetch (leave empty for all)
          </p>
          <input
            type="number"
            value={maxRecords}
            onChange={(e) => setMaxRecords(e.target.value)}
            placeholder="100"
            min={1}
            max={10000}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          />
        </div>
        </div>
      )}
    </div>
  );
}
