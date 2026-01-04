'use client';

import { UploadBox } from '@/components/UploadBox';
import { parseFile } from '@/utils/fileParser';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

// Store files in memory using a Map
export const fileCache = new Map<string, File>();

export default function IngestPage() {
  const router = useRouter();
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const handleFileSelect = async (file: File) => {
    setIsParsing(true);
    setError(null);
    
    try {
      // Parse file client-side for preview (no API call yet)
      const parsedData = await parseFile(file);
      
      // Generate a temporary preview ID (not a real job_id yet)
      const previewId = `preview_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Store file in memory cache instead of sessionStorage
      fileCache.set(previewId, file);
      
      // Store metadata and parsed data in sessionStorage for preview page
      const fileData = {
        previewId,
        fileName: file.name,
        fileType: file.name.split('.').pop()?.toLowerCase(),
        fileSize: file.size,
        parsedData,
        uploadedAt: new Date().toISOString(),
      };
      
      // Store only metadata in sessionStorage (not the file itself)
      sessionStorage.setItem(`preview_data_${previewId}`, JSON.stringify(fileData));
      
      // Navigate to preview with preview_id in params
      router.push(`/preview/${previewId}`);
    } catch (err) {
      console.error('File parsing failed:', err);
      setError(err instanceof Error ? err : new Error('Failed to parse file'));
    } finally {
      setIsParsing(false);
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
      
      {isParsing && (
        <p className="mt-4 text-sm text-gray-500 center">
          Processing...
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

