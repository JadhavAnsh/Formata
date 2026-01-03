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
    <div className="space-y-6">
      <div>
        <Label htmlFor="file-input">Select File</Label>
        <Input
          id="file-input"
          type="file"
          accept=".csv,.json"
          onChange={handleFileChange}
          className="mt-2"
        />
        {selectedFile && (
          <p className="mt-2 text-sm text-muted-foreground">
            Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
          </p>
        )}
      </div>

      <div>
        <Label htmlFor="target-format">Convert To</Label>
        <Select
          value={targetFormat}
          onValueChange={(value) => setTargetFormat(value as 'csv' | 'json')}
        >
          <SelectTrigger id="target-format" className="mt-2 w-full">
            <SelectValue placeholder="Select format" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="json">JSON</SelectItem>
            <SelectItem value="csv">CSV</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {error && (
        <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm">
          {error}
        </div>
      )}

      <div className="flex gap-4">
        <Button
          onClick={handleConvert}
          disabled={!selectedFile || isConverting}
        >
          {isConverting ? 'Converting...' : 'Convert'}
        </Button>

        {downloadUrl && (
          <Button variant="outline" onClick={handleDownload}>
            Download Converted File
          </Button>
        )}
      </div>
    </div>
  );
}

