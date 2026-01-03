'use client';

import { useCallback, useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Upload } from 'lucide-react';

interface UploadBoxProps {
  onFileSelect?: (file: File) => void;
}

export function UploadBox({ onFileSelect }: UploadBoxProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file && onFileSelect) {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file && onFileSelect) {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleButtonClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <div className="w-full max-w-3xl">
      <div className="rounded-xl bg-card p-4 sm:p-6">
        <div
          className={`border-2 border-dashed rounded-lg p-8 sm:p-12 text-center transition-colors ${
            isDragging ? 'border-primary bg-primary/5' : 'border-border'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <div className="flex flex-col items-center gap-6">
            <div className="flex items-center justify-center">
              <div className="rounded-full bg-muted p-4">
                <div className="rounded-lg bg-background p-3">
                  <Upload className="w-6 h-6 text-foreground" />
                </div>
              </div>
            </div>
            
            <div className="flex flex-col gap-2">
              <p className="text-foreground text-base font-medium">
                Drag and drop your file here
              </p>
              <p className="text-muted-foreground text-sm">
                CSV, JSON, XLSX up to 50MB
              </p>
            </div>
            
            <Input
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
              accept=".csv,.json,.xlsx,.xls"
            />
            <Button 
              variant="outline" 
              type="button"
              onClick={handleButtonClick}
              className="cursor-pointer"
            >
              Select File
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

