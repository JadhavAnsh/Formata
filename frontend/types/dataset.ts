/**
 * Dataset models and types
 */

export type DataType = 'string' | 'number' | 'date' | 'boolean' | 'null';

export interface ColumnMetadata {
  name: string;
  type: DataType;
  nullable?: boolean;
  sampleValues?: any[];
}

export interface Dataset {
  columns: ColumnMetadata[];
  rows: Array<Record<string, any>>;
  rowCount: number;
  metadata?: {
    source?: string;
    processedAt?: string;
    transformations?: string[];
  };
}

