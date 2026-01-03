'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { UploadBox } from '@/components/UploadBox';
import { useUpload } from '@/hooks/useUpload';
import { parseFile } from '@/utils/fileParser';

export default function IngestPage() {
  const router = useRouter();
  const [isParsing, setIsParsing] = useState(false);
  const [parseError, setParseError] = useState<Error | null>(null);
  const { upload, isUploading, error } = useUpload({
    onSuccess: (job) => {
      router.push(`/preview/${job.id}`);
    },
  });

  const handleFileSelect = async (file: File) => {
    // Try to parse file client-side first (temporary bypass)
    setIsParsing(true);
    setParseError(null);
    
    try {
      const parsedData = await parseFile(file);
      
      // Generate a temporary job ID
      const tempJobId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Store parsed data in localStorage
      const fileData = {
        jobId: tempJobId,
        fileName: file.name,
        fileType: file.name.split('.').pop()?.toLowerCase(),
        parsedData,
        uploadedAt: new Date().toISOString(),
      };
      
      localStorage.setItem(`preview_data_${tempJobId}`, JSON.stringify(fileData));
      
      // Navigate to preview with temp job ID
      router.push(`/preview/${tempJobId}`);
    } catch (err) {
      // If parsing fails, try the API upload
      console.warn('Client-side parsing failed, trying API upload:', err);
      setParseError(err instanceof Error ? err : new Error('Failed to parse file'));
      
      // Fall back to API upload
      try {
        await upload(file);
      } catch (uploadErr) {
        // Both failed
        console.error('Both client-side parsing and API upload failed');
      }
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
      
      {(isUploading || isParsing) && (
        <p className="mt-4 text-sm text-gray-500 center">
          {isParsing ? 'Parsing file...' : 'Uploading...'}
        </p>
      )}
      
      {(error || parseError) && (
        <p className="mt-4 text-sm text-red-500 center">
          {(error || parseError)?.message}
        </p>
      )}
    </div>
  );
}

