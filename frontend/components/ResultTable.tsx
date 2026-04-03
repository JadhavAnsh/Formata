'use client';

import { useMemo } from 'react';
import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table';

interface ResultTableProps {
  data?: Array<Record<string, any>>;
  beforeData?: Array<Record<string, any>>;
  afterData?: Array<Record<string, any>>;
}

const MAX_RENDER_ROWS = 2000;

function isMissing(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  return false;
}

export function ResultTable({ data, beforeData, afterData }: ResultTableProps) {
  const rawRows = useMemo(() => beforeData || [], [beforeData]);
  const fullData = useMemo(() => afterData || data || [], [afterData, data]);
  const displayData = useMemo(() => fullData.slice(0, MAX_RENDER_ROWS), [fullData]);
  const columns = Object.keys(displayData[0] || {});
  const columnHelper = createColumnHelper<Record<string, any>>();
  const tableColumns = useMemo(
    () =>
      columns.map((col) =>
        columnHelper.accessor((row) => row[col], {
          id: col,
          header: () => col,
          cell: (ctx) => {
            const rowIndex = ctx.row.index;
            const nextValue = ctx.getValue();
            const prevValue = rawRows[rowIndex]?.[col];

            const nextString = String(nextValue ?? '');
            const prevString = String(prevValue ?? '');
            const changed = prevString !== nextString;
            const imputed = isMissing(prevValue) && !isMissing(nextValue);
            const corrected = changed && !imputed;

            return (
              <span
                className={
                  imputed
                    ? 'inline-block px-2 py-0.5 rounded bg-emerald-100 text-emerald-900'
                    : corrected
                      ? 'inline-block px-2 py-0.5 rounded bg-orange-100 text-orange-900'
                      : undefined
                }
                title={
                  imputed
                    ? 'Imputed value'
                    : corrected
                      ? `Corrected: ${prevString} -> ${nextString}`
                      : undefined
                }
              >
                {nextString}
              </span>
            );
          },
        })
      ),
    [columnHelper, columns, rawRows]
  );

  const table = useReactTable({
    data: displayData,
    columns: tableColumns,
    getCoreRowModel: getCoreRowModel(),
  });

  const rows = table.getRowModel().rows;

  if (displayData.length === 0) {
    return <p className="text-muted-foreground">No data to display</p>;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded bg-emerald-100 border" /> Imputed
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded bg-orange-100 border" /> Corrected
        </span>
      </div>
      {fullData.length > MAX_RENDER_ROWS && (
        <div className="text-xs text-muted-foreground">
          Showing first {MAX_RENDER_ROWS} rows out of {fullData.length} for responsive rendering.
        </div>
      )}
      <div className="overflow-x-auto overflow-y-auto h-[70vh] border rounded-lg">
      <table className="w-full border-collapse border">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="border p-2 text-left bg-muted sticky top-0 z-10">
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
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="border p-2">
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

