import { apiGet, apiRequest } from './api';
import type { Job } from '@/types/job';

/**
 * Service for managing and listing jobs
 */
export const jobsService = {
  /**
   * List all jobs for the current user
   */
  async listJobs(jwt?: string): Promise<Job[]> {
    try {
      const response = await apiGet<any[]>('/jobs', jwt);
      
      // Normalize to frontend Job type
      return response.map(job => ({
        id: job.job_id,
        job_id: job.job_id,
        filename: job.file_name,
        status: job.status,
        progress: job.progress * 100,
        createdAt: job.created_at,
        updatedAt: job.completed_at || job.created_at,
        metadata: job.metadata
      }));
    } catch (error) {
      console.error('Error listing jobs:', error);
      throw error;
    }
  },

  /**
   * Get summary of job counts by status
   */
  async getSummary(jwt?: string): Promise<Record<string, number>> {
    return apiGet<Record<string, number>>('/jobs/status/summary', jwt);
  },

  /**
   * Delete a job
   */
  async deleteJob(jobId: string, jwt?: string): Promise<void> {
    await apiRequest(`/jobs/${jobId}`, { method: 'DELETE' }, jwt);
  }
};
