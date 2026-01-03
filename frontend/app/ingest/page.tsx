'use client';

import { useRouter } from 'next/navigation';
import { UploadBox } from '@/components/UploadBox';
import { useUpload } from '@/hooks/useUpload';

export default function IngestPage() {
  const router = useRouter();
  const { upload, isUploading, error } = useUpload({
    onSuccess: (job) => {
      router.push(`/process/${job.id}`);
    },
  });

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
          onFileSelect={(file) => {
            upload(file);
          }}
        />
      </div>
      
      {isUploading && (
        <p className="mt-4 text-sm text-gray-500 center">Uploading...</p>
      )}
      
      {error && <p className="mt-4 text-sm text-red-500 center">{error.message}</p>}
    </div>
  );
}

