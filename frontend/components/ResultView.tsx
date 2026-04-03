'use client';

import { ResultTable } from '@/components/ResultTable';

interface ResultViewProps {
  beforeRows?: Array<Record<string, any>>;
  afterRows?: Array<Record<string, any>>;
}

export function ResultView({ beforeRows = [], afterRows = [] }: ResultViewProps) {
  if (!afterRows.length) {
    return <p className="text-muted-foreground">No processed data to display.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        Visual Diff compares raw vs processed data with cell provenance highlights.
      </div>
      <ResultTable beforeData={beforeRows} afterData={afterRows} />
    </div>
  );
}
