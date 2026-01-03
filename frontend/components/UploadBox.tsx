'use client';

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface UploadBoxProps {
  onFileSelect?: (file: File) => void;
}

export function UploadBox({ onFileSelect }: UploadBoxProps) {
  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file && onFileSelect) {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  return (
    <div className="border-2 border-dashed rounded-lg p-8 text-center">
      <input
        type="file"
        onChange={handleFileChange}
        className="hidden"
        id="file-upload"
      />
      <label htmlFor="file-upload">
        <Button variant="outline" asChild>
          <span>Choose File</span>
        </Button>
      </label>
      <p className="mt-4 text-sm text-muted-foreground">
        Drag and drop your file here, or click to browse
      </p>
    </div>
  );
}

