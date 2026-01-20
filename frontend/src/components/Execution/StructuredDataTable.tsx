/**
 * Structured Data Table Component
 * 
 * Displays structured data (list of dictionaries) as an interactive table
 * in the Execution Panel.
 */

import React, { useState, useMemo } from 'react';
import { Table2, Download, Search, ChevronUp, ChevronDown, FileSpreadsheet } from 'lucide-react';
import { cn } from '@/utils/cn';

interface StructuredDataTableProps {
  data: any;
  schema?: {
    columns?: string[];
    row_count?: number;
    column_count?: number;
  };
  maxRows?: number;
  className?: string;
}

export function StructuredDataTable({ 
  data, 
  schema, 
  maxRows = 100,
  className 
}: StructuredDataTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 20;

  // Detect if data is structured (list of dicts)
  const isStructuredData = useMemo(() => {
    if (!Array.isArray(data)) return false;
    if (data.length === 0) return false;
    return typeof data[0] === 'object' && data[0] !== null && !Array.isArray(data[0]);
  }, [data]);

  // Extract table data
  const tableData = useMemo(() => {
    if (!isStructuredData) return null;

    let processed = [...data];

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      processed = processed.filter(row => {
        return Object.values(row).some(value => 
          String(value).toLowerCase().includes(term)
        );
      });
    }

    // Apply sorting
    if (sortColumn) {
      processed.sort((a, b) => {
        const aVal = a[sortColumn];
        const bVal = b[sortColumn];
        
        // Handle null/undefined
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;
        
        // Compare values
        const comparison = String(aVal).localeCompare(String(bVal), undefined, { 
          numeric: true, 
          sensitivity: 'base' 
        });
        
        return sortDirection === 'asc' ? comparison : -comparison;
      });
    }

    return processed;
  }, [data, isStructuredData, searchTerm, sortColumn, sortDirection]);

  // Get columns
  const columns = useMemo(() => {
    if (!tableData || tableData.length === 0) return [];
    
    // Get all unique keys from all rows
    const allKeys = new Set<string>();
    tableData.forEach(row => {
      Object.keys(row).forEach(key => allKeys.add(key));
    });
    
    // Use schema columns if available, otherwise use all keys
    if (schema?.columns && schema.columns.length > 0) {
      return schema.columns.filter(col => allKeys.has(col));
    }
    
    return Array.from(allKeys).sort();
  }, [tableData, schema]);

  // Pagination
  const totalPages = Math.ceil((tableData?.length || 0) / rowsPerPage);
  const paginatedData = useMemo(() => {
    if (!tableData) return [];
    const start = (currentPage - 1) * rowsPerPage;
    return tableData.slice(start, start + rowsPerPage);
  }, [tableData, currentPage, rowsPerPage]);

  // Handle sort
  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  // Export to CSV
  const handleExportCSV = () => {
    if (!tableData || tableData.length === 0) return;

    // Create CSV content
    const headers = columns;
    const rows = tableData.map(row => 
      headers.map(header => {
        const value = row[header];
        // Escape quotes and wrap in quotes if contains comma or newline
        const str = String(value ?? '');
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      })
    );

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `data_export_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!isStructuredData) {
    return null;
  }

  const totalRows = tableData?.length || 0;
  const displayRows = Math.min(totalRows, maxRows);

  return (
    <div className={cn("space-y-3", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Table2 className="w-4 h-4 text-amber-400" />
          <div className="text-xs font-semibold text-amber-400">
            Structured Data ({displayRows.toLocaleString()} {displayRows === 1 ? 'row' : 'rows'})
          </div>
          {schema?.column_count && (
            <div className="text-xs text-slate-500">
              • {schema.column_count} {schema.column_count === 1 ? 'column' : 'columns'}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="text-xs px-2 py-1 rounded hover:bg-white/10 transition-colors text-slate-400 hover:text-white flex items-center gap-1"
            title="Export to CSV"
          >
            <Download className="w-3 h-3" />
            CSV
          </button>
        </div>
      </div>

      {/* Search */}
      {totalRows > 5 && (
        <div className="relative">
          <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search rows..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1); // Reset to first page on search
            }}
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-black/40 border border-white/10 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
          />
        </div>
      )}

      {/* Table */}
      <div className="border border-white/10 rounded-lg overflow-hidden bg-black/20">
        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full text-xs">
            <thead className="bg-white/5 sticky top-0">
              <tr>
                {columns.map(column => (
                  <th
                    key={column}
                    className="px-3 py-2 text-left text-slate-400 font-medium cursor-pointer hover:bg-white/10 transition-colors select-none"
                    onClick={() => handleSort(column)}
                  >
                    <div className="flex items-center gap-1">
                      <span>{column}</span>
                      {sortColumn === column && (
                        sortDirection === 'asc' ? (
                          <ChevronUp className="w-3 h-3" />
                        ) : (
                          <ChevronDown className="w-3 h-3" />
                        )
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {paginatedData.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-3 py-8 text-center text-slate-500">
                    {searchTerm ? 'No rows match your search' : 'No data available'}
                  </td>
                </tr>
              ) : (
                paginatedData.map((row, idx) => (
                  <tr 
                    key={idx} 
                    className="hover:bg-white/5 transition-colors"
                  >
                    {columns.map(column => (
                      <td 
                        key={column} 
                        className="px-3 py-2 text-slate-300"
                      >
                        {row[column] != null ? String(row[column]) : (
                          <span className="text-slate-600 italic">—</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-3 py-2 border-t border-white/10 bg-white/5 flex items-center justify-between">
            <div className="text-xs text-slate-400">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-2 py-1 text-xs rounded hover:bg-white/10 transition-colors text-slate-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-2 py-1 text-xs rounded hover:bg-white/10 transition-colors text-slate-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Info */}
      {totalRows >= maxRows && (
        <div className="text-xs text-slate-500 text-center">
          Showing first {maxRows.toLocaleString()} rows. Export to CSV to see all data.
        </div>
      )}
    </div>
  );
}
