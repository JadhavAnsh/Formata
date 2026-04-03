import { ApiRequestError, apiRequest } from './api';
import type { Job } from '@/types/job';

/**
 * Service for checking job status
 */
export const statusService = {
  /**
   * Get the current status of a job
   */
  async getJobStatus(jobId: string): Promise<Job> {
    try {
      console.log('Fetching job status for:', jobId);
      const response = await apiRequest<any>(`/status/${jobId}`);
      console.log('Job status response:', response);
      
      // Normalize backend response to match frontend Job type
      // Backend returns: job_id, file_name, created_at, progress (0.0-1.0), errors (array), result (dict)
      // Frontend expects: id, job_id, filename, createdAt, updatedAt, progress (0-100), error (string), result (dict)
      const normalized: Job = {
        job_id: response.job_id || jobId,
        id: response.job_id || jobId,
        status: response.status || 'pending',
        progress: response.progress !== undefined 
          ? (response.progress <= 1 ? response.progress * 100 : response.progress)
          : 0,
        filename: response.file_name,
        createdAt: response.created_at || new Date().toISOString(),
        updatedAt: response.completed_at || response.started_at || response.created_at || new Date().toISOString(),
        fileSize: response.metadata?.file_size,
        metadata: response.metadata,
        error: Array.isArray(response.errors) && response.errors.length > 0
          ? response.errors.join(', ')
          : response.errors || undefined,
        result: response.result, // Include result data from backend
      };
      
      console.log('Normalized job:', normalized);
      return normalized;
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 404) {
        console.warn(`Job ${jobId} not found. The backend may have restarted or the job state expired.`);
        throw new Error(`Job ${jobId} not found. Please upload the file again to start a new job.`);
      }

      console.error('Error fetching job status:', error);
      throw error;
    }
  },
};

