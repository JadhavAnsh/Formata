interface ValidationError {
  row?: number;
  column?: string;
  message: string;
  value?: any;
}

interface ErrorTableProps {
  errors?: ValidationError[];
}

export function ErrorTable({ errors = [] }: ErrorTableProps) {
  if (errors.length === 0) {
    return <p className="text-muted-foreground">No validation errors</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border">
        <thead>
          <tr>
            <th className="border p-2 text-left">Row</th>
            <th className="border p-2 text-left">Column</th>
            <th className="border p-2 text-left">Message</th>
            <th className="border p-2 text-left">Value</th>
          </tr>
        </thead>
        <tbody>
          {errors.map((error, idx) => (
            <tr key={idx} className="text-destructive">
              <td className="border p-2">{error.row ?? '-'}</td>
              <td className="border p-2">{error.column ?? '-'}</td>
              <td className="border p-2">{error.message}</td>
              <td className="border p-2">{String(error.value ?? '-')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

