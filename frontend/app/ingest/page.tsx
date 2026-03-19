'use client';

import { UploadBox } from '@/components/UploadBox';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { ingestService } from '@/services/ingest.service';
import { useAuth } from '@/context/AuthContext';

export default function IngestPage() {
  const router = useRouter();
  const { getJwt } = useAuth();
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const handleFileSelect = async (file: File) => {
    setIsUploading(true);
    setError(null);
    
    try {
      // Get JWT for backend authentication
      const jwt = await getJwt();
      if (!jwt) {
        throw new Error('Authentication failed. Please log in again.');
      }
      
      // 1. Upload to Appwrite and 2. Register with backend
      const job = await ingestService.uploadFile(file, jwt);
      
      const jobId = job.job_id || job.id;
      if (!jobId) {
        throw new Error('Failed to create job');
      }
      
      // Navigate to preview with the REAL job_id from backend
      router.push(`/preview/${jobId}`);
    } catch (err) {
      console.error('File upload failed:', err);
      setError(err instanceof Error ? err : new Error('Failed to upload file'));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="container mx-auto mt-16 sm:mt-20 px-4 sm:px-6 max-w-4xl flex flex-col items-center">
      <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold italic mb-4 sm:mb-6 text-center">
        MESSY DATA TO STRUCTURED DATA
      </h1>
      <p className="text-center text-gray-500 mb-6 sm:mb-8 text-base sm:text-lg leading-relaxed max-w-2xl">
        Upload raw data from CSV, Excel, or JSON and let Formata clean, normalize, and structure it automatically.
      </p>
      
      <div className="w-full max-w-2xl">
        <UploadBox
          onFileSelect={handleFileSelect}
        />
      </div>
      
      {isUploading && (
        <p className="mt-4 text-sm text-gray-500 center">
          Uploading to Appwrite...
        </p>
      )}
      
      {error && (
        <p className="mt-4 text-sm text-red-500 center">
          {error.message}
        </p>
      )}
    </div>
  );
}

