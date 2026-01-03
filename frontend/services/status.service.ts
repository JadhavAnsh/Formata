import { apiRequest } from './api';
import type { Job } from '@/types/job';

/**
 * Service for checking job status
 */
export const statusService = {
  /**
   * Get the current status of a job
   */
  async getJobStatus(jobId: string): Promise<Job> {
    return apiRequest(`/status/${jobId}`);
  },
};

