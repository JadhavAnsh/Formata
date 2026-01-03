/**
 * Error and validation result schemas
 */

export interface ValidationError {
  row?: number;
  column?: string;
  message: string;
  value?: any;
  code?: string;
  severity?: 'error' | 'warning' | 'info';
}

export interface ProcessingError {
  message: string;
  code?: string;
  details?: Record<string, any>;
  timestamp?: string;
}

