import { storage } from '@/lib/appwrite';
import { ID } from 'appwrite';
import { apiPost } from './api';
import type { Job } from '@/types/job';

/**
 * Service for file ingestion/upload operations
 */
export const ingestService = {
  /**
   * Upload a file for processing
   */
  async uploadFile(file: File, jwt?: string, options?: {
    filters?: Record<string, any>;
    normalization?: Record<string, any>;
  }): Promise<Job> {
    try {
      // 1. Upload to Appwrite Storage
      const bucketId = process.env.NEXT_PUBLIC_APPWRITE_STORAGE_BUCKET_ID || '';
      if (!bucketId) {
        throw new Error('Appwrite Bucket ID not configured');
      }

      const fileResponse = await storage.createFile(
        bucketId,
        ID.unique(),
        file
      );

      const fileId = fileResponse.$id;

      // 2. Register with backend
      return apiPost('/ingest', {
        file_id: fileId,
        file_name: file.name,
        file_size: file.size,
        file_type: file.type || file.name.split('.').pop()
      }, jwt);
    } catch (error) {
      console.error('Ingest Service Error:', error);
      throw error;
    }
  },
};

