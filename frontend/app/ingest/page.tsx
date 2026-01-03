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
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">File Upload</h1>
      <p className="text-muted-foreground mb-6">
        Upload your data file for processing
      </p>
      
      <UploadBox
        onFileSelect={(file) => {
          upload(file);
        }}
      />
      
      {isUploading && (
        <p className="mt-4 text-sm text-muted-foreground">Uploading...</p>
      )}
      
      {error && (
        <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
          {error.message}
        </div>
      )}
    </div>
  );
}

