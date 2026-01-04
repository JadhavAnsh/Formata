/**
 * Job metadata and status types
 */

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface Job {
  job_id: string;
  id: string;
  status: JobStatus;
  progress?: number; // 0-100
  createdAt: string;
  updatedAt: string;
  filename?: string;
  fileSize?: number;
  metadata?: Record<string, any>;
  error?: string;
  result?: Record<string, any>; // Result data from processing
}

