'use client';

import { useMemo } from 'react';
import { useReactTable, getCoreRowModel, flexRender, createColumnHelper } from '@tanstack/react-table';

interface PreviewTableProps {
  data?: Array<Record<string, any>>;
  isLoading?: boolean;
  rowCount?: number;
  totalRows?: number;
  columns?: string[];
  missingByColumn?: Record<string, { count: number; percentage: number }>;
}

const MAX_CELL_PREVIEW_LENGTH = 120;

function stringifyCell(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }

  if (typeof value === 'string') {
    return value;
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function isMissingValue(value: unknown): boolean {
  if (value === null || value === undefined) {
    return true;
  }

  if (typeof value === 'string') {
    return value.trim() === '';
  }

  return false;
}

export function PreviewTable({ data, isLoading, rowCount, totalRows, columns, missingByColumn }: PreviewTableProps) {
  const safeData = data ?? [];
  const resolvedColumns = columns && columns.length > 0 ? columns : Object.keys(safeData[0] || {});
  const columnHelper = createColumnHelper<Record<string, any>>();
  const tableColumns = useMemo(
    () =>
      resolvedColumns.map((col) =>
        columnHelper.accessor((row) => row[col], {
          id: col,
          header: () => (
            <div className="flex flex-col gap-1">
              <span>{col}</span>
              {missingByColumn?.[col] && (
                <span className="text-[11px] font-normal text-muted-foreground">
                  Missing: {missingByColumn[col].count} ({missingByColumn[col].percentage.toFixed(1)}%)
                </span>
              )}
            </div>
          ),
          cell: (ctx) => {
            const rawValue = ctx.getValue();
            const cellValue = stringifyCell(rawValue);
            const isMissing = isMissingValue(rawValue);
            const isLong = cellValue.length > MAX_CELL_PREVIEW_LENGTH;
            const displayValue = isLong
              ? `${cellValue.slice(0, MAX_CELL_PREVIEW_LENGTH)}...`
              : cellValue;

            if (isMissing) {
              return (
                <span className="inline-block px-2 py-0.5 rounded bg-amber-100 text-amber-900 text-xs font-medium">
                  MISSING
                </span>
              );
            }

            return <span title={isLong ? cellValue : undefined}>{displayValue}</span>;
          },
        })
      ),
    [columnHelper, resolvedColumns, missingByColumn]
  );

  const table = useReactTable({
    data: safeData,
    columns: tableColumns,
    getCoreRowModel: getCoreRowModel(),
  });

  const rows = table.getRowModel().rows;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-muted-foreground">Loading data...</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-muted-foreground">No data to display</p>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {(rowCount !== undefined || totalRows !== undefined) && (
        <div className="text-sm text-muted-foreground">
          Showing {rowCount ?? data.length} {totalRows !== undefined && totalRows !== rowCount && `of ${totalRows}`} rows
        </div>
      )}
      {missingByColumn && Object.keys(missingByColumn).length > 0 && (
        <div className="text-xs text-muted-foreground">
          Missing values shown per column header as count and percentage.
        </div>
      )}
      <div className="themed-scrollbar border rounded-lg h-[70vh] overflow-y-auto overflow-x-auto">
        <table className="w-full border-collapse">
          <thead className="bg-muted sticky top-0 z-10">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="border p-3 text-left font-semibold text-sm whitespace-nowrap">
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="hover:bg-muted/50 transition-colors">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="border p-3 text-sm align-top max-w-[28rem] whitespace-normal break-words">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

