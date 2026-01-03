import { apiUpload, apiRequest } from './api';

export interface ConvertResult {
  data: string;
  format: 'csv' | 'json';
  filename: string;
}

/**
 * Service for file conversion operations (CSV ↔ JSON)
 */
export const convertService = {
  /**
   * Convert a file from one format to another
   */
  async convertFile(
    file: File,
    targetFormat: 'csv' | 'json'
  ): Promise<ConvertResult> {
    return apiUpload('/convert', file, { targetFormat });
  },

  /**
   * Download converted file
   */
  async downloadConvertedFile(jobId: string): Promise<Blob> {
    const response = await fetch(`/api/convert/${jobId}/download`);
    if (!response.ok) {
      throw new Error('Failed to download file');
    }
    return response.blob();
  },
};

