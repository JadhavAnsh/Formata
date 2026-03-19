import { apiRequest } from './api';
import type { Job } from '@/types/job';

/**
 * Service for checking job status
 */
export const statusService = {
  /**
   * Get the current status of a job
   */
  async getJobStatus(jobId: string, jwt?: string): Promise<Job> {
    try {
      console.log('Fetching job status for:', jobId);
      const response = await apiRequest<any>(`/status/${jobId}`, {}, jwt);
      
      // Normalize backend response to match frontend Job type
      const normalized: Job = {
        job_id: response.job_id || jobId,
        id: response.job_id || jobId,
        status: response.status || 'pending',
        progress: response.progress !== undefined 
          ? (response.progress <= 1 ? response.progress * 100 : response.progress)
          : 0,
        // Match the hyphenated name we used in Appwrite
        filename: response['file-name'] || response.file_name,
        createdAt: response.created_at || new Date().toISOString(),
        updatedAt: response.completed_at || response.started_at || response.created_at || new Date().toISOString(),
        metadata: typeof response.metadata === 'string' ? JSON.parse(response.metadata) : response.metadata,
        error: Array.isArray(response.errors) && response.errors.length > 0
          ? response.errors.join(', ')
          : response.errors || undefined,
        result: response.result,
      };
      
      return normalized;
    } catch (error) {
      console.error('Error fetching job status:', error);
      throw error;
    }
  },
};
