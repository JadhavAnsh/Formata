import { apiUpload } from './api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

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
   * Convert CSV file to JSON
   */
  async csvToJson(file: File): Promise<Blob> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/convert/csv-to-json`, {
      method: 'POST',
      headers: {
        ...(API_KEY && { 'X-API-Key': API_KEY }),
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Failed to convert CSV to JSON: ${response.statusText}`);
    }

    return response.blob();
  },

  /**
   * Convert JSON file to CSV
   */
  async jsonToCsv(file: File): Promise<Blob> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/convert/json-to-csv`, {
      method: 'POST',
      headers: {
        ...(API_KEY && { 'X-API-Key': API_KEY }),
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Failed to convert JSON to CSV: ${response.statusText}`);
    }

    return response.blob();
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

