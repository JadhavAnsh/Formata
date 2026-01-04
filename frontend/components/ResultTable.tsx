interface ResultTableProps {
  data?: Array<Record<string, any>>;
  beforeData?: Array<Record<string, any>>;
  afterData?: Array<Record<string, any>>;
}

export function ResultTable({ data, beforeData, afterData }: ResultTableProps) {
  const displayData = data || beforeData || afterData || [];

  if (displayData.length === 0) {
    return <p className="text-muted-foreground">No data to display</p>;
  }

  const columns = Object.keys(displayData[0] || {});

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col} className="border p-2 text-left">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayData.map((row, idx) => (
            <tr key={idx}>
              {columns.map((col) => (
                <td key={col} className="border p-2">
                  {String(row[col] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

