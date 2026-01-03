'use client';

interface PreviewTableProps {
  data?: Array<Record<string, any>>;
  isLoading?: boolean;
  rowCount?: number;
  totalRows?: number;
}

export function PreviewTable({ data, isLoading, rowCount, totalRows }: PreviewTableProps) {
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

  const columns = Object.keys(data[0] || {});

  return (
    <div className="space-y-4">
      {(rowCount !== undefined || totalRows !== undefined) && (
        <div className="text-sm text-muted-foreground">
          Showing {rowCount ?? data.length} {totalRows !== undefined && totalRows !== rowCount && `of ${totalRows}`} rows
        </div>
      )}
      <div className="themed-scrollbar border rounded-lg h-[70vh] overflow-y-auto overflow-x-auto">
        <table className="w-full border-collapse">
          <thead className="bg-muted sticky top-0 z-10">
            <tr>
              {columns.map((col) => (
                <th key={col} className="border p-3 text-left font-semibold text-sm whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-muted/50 transition-colors">
                {columns.map((col) => (
                  <td key={col} className="border p-3 text-sm whitespace-nowrap">
                    {String(row[col] ?? '')}
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

