import { apiPost, apiGet } from './api';

export interface VectorRequest {
  method: 'hybrid' | 'text_only' | 'numeric';
  provider: 'local' | 'gemini';
}

export interface VectorInfo {
  status: string;
  job_id: string;
  vector_shape: number[];
  n_samples: number;
  n_features: number;
  method: string;
  provider: string;
  pkl_file_id: string;
  h5_file_id: string;
  message: string;
}

/**
 * Service for vector operations
 */
export const vectorService = {
  /**
   * Generate vectors for a completed job
   */
  async generateVectors(jobId: string, request: VectorRequest, jwt?: string): Promise<VectorInfo> {
    return apiPost(`/vectors/${jobId}/generate`, request, jwt);
  },

  /**
   * Get vector info for a job
   */
  async getVectorInfo(jobId: string, jwt?: string): Promise<any> {
    return apiGet(`/vectors/${jobId}/info`, jwt);
  }
};
