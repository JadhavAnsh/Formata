import type { Dataset } from '@/types/dataset';
import type { ValidationError } from '@/types/error';
import { statusService } from './status.service';

export interface ProcessingResult {
  jobId: string;
  beforeData?: Dataset;
  afterData?: Dataset;
  errors?: ValidationError[];
  metadata?: Record<string, any>;
}

export interface ProfileReport {
  job_id: string;
  report_path: string;
  content_type: string;
  content: string;
}

/**
 * Service for fetching processing results
 */
export const resultService = {
  /**
   * Get the profile report HTML content for a job
   */
  async getProfileReport(jobId: string): Promise<ProfileReport> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';
    const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';
    
    const url = `${API_BASE_URL}/profile/${jobId}`;
    
    const response = await fetch(url, {
      headers: {
        ...(API_KEY && { 'X-API-Key': API_KEY }),
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch profile report: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Download the cleaned dataset file for a job
   */
  async downloadResult(jobId: string): Promise<void> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';
    const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';
    
    const url = `${API_BASE_URL}/result/${jobId}/download`;
    
    const response = await fetch(url, {
      headers: {
        ...(API_KEY && { 'X-API-Key': API_KEY }),
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to download: ${response.statusText}`);
    }
    
    // Get filename from Content-Disposition header if available
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `formata-clean-${jobId}.csv`;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^"\n]+)"?/);
      if (match) {
        filename = match[1];
      }
    }
    
    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(downloadUrl);
  },

  /**
   * Download the vector pickle file for a job
   */
  async downloadVectorPkl(jobId: string): Promise<void> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';
    const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';
    
    const url = `${API_BASE_URL}/vectors/${jobId}/download?format=pkl`;
    
    const response = await fetch(url, {
      headers: {
        ...(API_KEY && { 'X-API-Key': API_KEY }),
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to download vector file: ${response.statusText}`);
    }
    
    // Get filename from Content-Disposition header if available
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `vectors_${jobId}.pkl`;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^"\n]+)"?/);
      if (match) {
        filename = match[1];
      }
    }
    
    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(downloadUrl);
  },

  /**
   * Get processing results for a job
   * Results are stored in the job's result field from the status endpoint
   */
  async getResults(jobId: string): Promise<ProcessingResult> {
    try {
      // Get job status which includes the result field
      const job = await statusService.getJobStatus(jobId);
      
      // Extract result data from job.result
      const resultData = job.result || job.metadata?.result;
      
      if (!resultData) {
        throw new Error('Result data not available yet. Job may still be processing.');
      }
      
      // Normalize the result data to match ProcessingResult interface
      return {
        jobId: job.job_id || job.id || jobId,
        beforeData: resultData.beforeData || resultData.before_data,
        afterData: resultData.afterData || resultData.after_data || resultData.data,
        errors: Array.isArray(resultData.errors) 
          ? resultData.errors.map((err: any) => ({
              row: err.row || err.row_index || 0,
              column: err.column || err.column_name || '',
              message: err.message || err.error || String(err),
              value: err.value,
              code: err.code || 'VALIDATION_ERROR',
              severity: err.severity || 'error',
            }))
          : resultData.errors,
        metadata: resultData.metadata || job.metadata,
      };
    } catch (error) {
      console.error('Error fetching results:', error);
      throw error;
    }
  },
};

