import { apiRequest } from './api';
import type { Job } from '@/types/job';

/**
 * Service for processing operations
 */
export const processService = {
  /**
   * Start processing a job
   * @param jobId - The job ID to process
   * @param options - Processing options including filters
   */
  async startProcessing(jobId: string, options?: {
    filters?: Record<string, any>;
    normalize?: boolean;
    remove_duplicates?: boolean;
    remove_outliers?: boolean;
    missing_data_strategy?: Record<string, string>;
    default_missing_strategy?: string;
    handle_missing_data?: boolean;
    enable_auto_schema?: boolean;
    enable_drift_detection?: boolean;
    enable_profiles?: boolean;
    enable_vectorization?: boolean;
    result_preview_rows?: number;
  }): Promise<Job> {
    // Build request body matching ProcessConfig from backend
    const body: {
      filters?: Record<string, any>;
      normalize?: boolean;
      remove_duplicates?: boolean;
      remove_outliers?: boolean;
      missing_data_strategy?: Record<string, string>;
      default_missing_strategy?: string;
      handle_missing_data?: boolean;
      enable_auto_schema?: boolean;
      enable_drift_detection?: boolean;
      enable_profiles?: boolean;
      enable_vectorization?: boolean;
      result_preview_rows?: number;
    } = {};
    
    if (options?.filters) {
      body.filters = options.filters;
    }
    if (options?.normalize !== undefined) {
      body.normalize = options.normalize;
    }
    if (options?.remove_duplicates !== undefined) {
      body.remove_duplicates = options.remove_duplicates;
    }
    if (options?.remove_outliers !== undefined) {
      body.remove_outliers = options.remove_outliers;
    }
    if (options?.missing_data_strategy) {
      body.missing_data_strategy = options.missing_data_strategy;
    }
    if (options?.default_missing_strategy !== undefined) {
      body.default_missing_strategy = options.default_missing_strategy;
    }
    if (options?.handle_missing_data !== undefined) {
      body.handle_missing_data = options.handle_missing_data;
    }
    if (options?.enable_auto_schema !== undefined) {
      body.enable_auto_schema = options.enable_auto_schema;
    }
    if (options?.enable_drift_detection !== undefined) {
      body.enable_drift_detection = options.enable_drift_detection;
    }
    if (options?.enable_profiles !== undefined) {
      body.enable_profiles = options.enable_profiles;
    }
    if (options?.enable_vectorization !== undefined) {
      body.enable_vectorization = options.enable_vectorization;
    }
    if (options?.result_preview_rows !== undefined) {
      body.result_preview_rows = options.result_preview_rows;
    }
    console.log(body);
    
    return apiRequest(`/process/${jobId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
};

