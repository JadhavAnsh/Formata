/**
 * Job metadata and status types
 */

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface Job {
  id: string;
  status: JobStatus;
  progress?: number; // 0-100
  createdAt: string;
  updatedAt: string;
  filename?: string;
  fileSize?: number;
  metadata?: Record<string, any>;
  error?: string;
}

