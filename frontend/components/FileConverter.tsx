'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { convertService } from '@/services/convert.service';

interface FileConverterProps {
  onConvert?: (result: { data: string; format: 'csv' | 'json'; filename: string }) => void;
}

export function FileConverter({ onConvert }: FileConverterProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [targetFormat, setTargetFormat] = useState<'csv' | 'json'>('json');
  const [isConverting, setIsConverting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        setSelectedFile(file);
        setError(null);
        // Auto-detect target format based on file extension
        const extension = file.name.split('.').pop()?.toLowerCase();
        if (extension === 'csv') {
          setTargetFormat('json');
        } else if (extension === 'json') {
          setTargetFormat('csv');
        }
      }
    },
    []
  );

  const handleConvert = useCallback(async () => {
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    setIsConverting(true);
    setError(null);
    setDownloadUrl(null);

    try {
      const result = await convertService.convertFile(selectedFile, targetFormat);
      
      // Create download URL from the result data
      const blob = new Blob([result.data], {
        type: targetFormat === 'json' ? 'application/json' : 'text/csv',
      });
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);
      
      onConvert?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Conversion failed');
    } finally {
      setIsConverting(false);
    }
  }, [selectedFile, targetFormat, onConvert]);

  const handleDownload = useCallback(() => {
    if (downloadUrl && selectedFile) {
      const extension = targetFormat === 'json' ? 'json' : 'csv';
      const originalName = selectedFile.name.split('.')[0];
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${originalName}.${extension}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(downloadUrl);
    }
  }, [downloadUrl, selectedFile, targetFormat]);

  return (
    <div className="w-full max-w-2xl space-y-6 flex flex-col items-center">
      <div className="w-full flex items-center gap-4">
        <Label htmlFor="file-input" className="whitespace-nowrap">Select File:</Label>
        <Input
          id="file-input"
          type="file"
          accept=".csv,.json"
          onChange={handleFileChange}
          className="flex-1"
        />
      </div>

      <div className="w-full flex items-center gap-4">
        <Label htmlFor="target-format" className="whitespace-nowrap">Convert To:</Label>
        <Select
          value={targetFormat}
          onValueChange={(value) => setTargetFormat(value as 'csv' | 'json')}
        >
          <SelectTrigger id="target-format" className="flex-1">
            <SelectValue placeholder="Select format" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="json">JSON</SelectItem>
            <SelectItem value="csv">CSV</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {error && (
        <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm w-full text-center">
          {error}
        </div>
      )}

      <div className="flex flex-col items-center gap-4 w-full">
        <Button
          onClick={handleConvert}
          disabled={!selectedFile || isConverting}
          className="w-full max-w-xs"
        >
          {isConverting ? 'Converting...' : 'Convert'}
        </Button>

        {downloadUrl && (
          <Button 
            variant="outline" 
            onClick={handleDownload}
            className="w-full max-w-xs"
          >
            Download
          </Button>
        )}
      </div>
    </div>
  );
}

