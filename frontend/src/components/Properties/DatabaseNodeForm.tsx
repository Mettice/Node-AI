/**
 * Enhanced Database Node Form Component
 * Provides a better UX than the generic SchemaForm for database operations
 */

import { useState, useEffect, useRef } from 'react';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import { DatabaseSelector } from './DatabaseSelector';
import { ConnectionStringInput } from './ConnectionStringInput';
import { testDatabaseConnection } from '@/services/nodes';
import { Database as DatabaseIcon, FileCode } from 'lucide-react';

interface DatabaseNodeFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  schema?: Record<string, any>;
}

const QUERY_TYPES = [
  { value: 'SELECT', label: 'SELECT', icon: 'database' },
  { value: 'INSERT', label: 'INSERT', icon: 'database' },
  { value: 'UPDATE', label: 'UPDATE', icon: 'database' },
  { value: 'DELETE', label: 'DELETE', icon: 'database' },
  { value: 'CUSTOM', label: 'Custom SQL', icon: 'database' },
];

export function DatabaseNodeForm({ initialData, onChange }: DatabaseNodeFormProps) {
  const [databaseType, setDatabaseType] = useState(initialData.database_type || 'sqlite');
  const [connectionString, setConnectionString] = useState(initialData.database_connection_string || '');
  const [queryType, setQueryType] = useState(initialData.query_type || 'SELECT');
  const [query, setQuery] = useState(initialData.database_query || '');
  
  const onChangeRef = useRef(onChange);
  
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  // Update parent when form changes
  useEffect(() => {
    const config: Record<string, any> = {
      database_type: databaseType,
      database_connection_string: connectionString,
      database_query: query,
      query_type: queryType,
    };

    onChangeRef.current(config);
  }, [databaseType, connectionString, query, queryType, onChange]);

  // Generate sample query based on query type
  const getSampleQuery = () => {
    switch (queryType) {
      case 'SELECT':
        return 'SELECT * FROM table_name LIMIT 10;';
      case 'INSERT':
        return 'INSERT INTO table_name (column1, column2) VALUES (\'value1\', \'value2\');';
      case 'UPDATE':
        return 'UPDATE table_name SET column1 = \'new_value\' WHERE id = 1;';
      case 'DELETE':
        return 'DELETE FROM table_name WHERE id = 1;';
      default:
        return '';
    }
  };

  const handleQueryTypeChange = (newType: string) => {
    setQueryType(newType);
    // If query is empty or matches previous sample, update to new sample
    if (!query || query === getSampleQuery()) {
      setQuery(getSampleQuery());
    }
  };

  return (
    <div className="space-y-4">
      {/* Database Type Selector */}
      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          Database Type <span className="text-red-400">*</span>
        </label>
        <DatabaseSelector
          currentDatabase={databaseType}
          onChange={setDatabaseType}
        />
      </div>

      {/* Connection Configuration */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <DatabaseIcon className="w-4 h-4" />
          <h3 className="text-sm font-semibold text-white">Connection Configuration</h3>
        </div>
        
        <div className="space-y-2">
          <ConnectionStringInput
            value={connectionString}
            onChange={setConnectionString}
            databaseType={databaseType}
            testConnection={testDatabaseConnection}
            placeholder={
              databaseType === 'sqlite' 
                ? 'database.db or /path/to/database.db'
                : databaseType === 'postgresql'
                ? 'postgresql://user:password@host:port/database'
                : 'mysql://user:password@host:port/database'
            }
          />
        </div>

      </div>

      {/* Query Configuration */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <FileCode className="w-4 h-4" />
          Query Configuration
        </h3>
        
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Query Type
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            Select query type for sample template (or use Custom for raw SQL)
          </p>
          <SelectWithIcons
            value={queryType}
            onChange={handleQueryTypeChange}
            options={QUERY_TYPES}
            placeholder="Select query type..."
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            SQL Query <span className="text-red-400">*</span>
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            SQL query to execute (can also come from previous node)
          </p>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={getSampleQuery() || 'Enter your SQL query here...'}
            rows={12}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all font-mono text-sm"
          />
          {queryType !== 'CUSTOM' && (
            <div className="flex items-start gap-2 p-2 bg-slate-800/50 rounded text-xs text-slate-300">
              <span className="text-purple-400">💡</span>
              <span>
                This is a sample query template. Modify it according to your needs. 
                For complex queries, select "Custom SQL" and write your own query.
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Query Builder (Future Enhancement) */}
      {queryType !== 'CUSTOM' && queryType === 'SELECT' && (
        <div className="space-y-2 p-3 bg-slate-800/30 border border-slate-700/50 rounded-lg">
          <p className="text-xs text-slate-400">
            <span className="text-purple-400">🚧</span> Visual query builder coming soon. 
            For now, use the SQL query editor above.
          </p>
        </div>
      )}
    </div>
  );
}

