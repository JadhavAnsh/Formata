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
    <div className="container mx-auto p-6 max-w-4xl flex flex-col items-center">
      <h1 className="text-3xl font-bold italic mb-6">MESSY DATA TO STRUCTURED DATA</h1>
      <p className="text-center text-gray-500 mb-8 text-lg leading-relaxed">
        Upload raw data from CSV, Excel, or JSON and let Formata clean, normalize, and structure it automatically.
      </p>
      
      <UploadBox
        onFileSelect={(file) => {
          upload(file);
        }}
      />
      
      {isUploading && (
        <p className="mt-4 text-sm text-gray-500 center">Uploading...</p>
      )}
      
      {error && <p className="mt-4 text-sm text-red-500 center">{error.message}</p>}
    </div>
  );
}

