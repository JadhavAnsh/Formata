'use client';

import { FileConverter } from '@/components/FileConverter';

export default function ConvertPage() {
  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">File Converter</h1>
      <p className="text-muted-foreground mb-6">
        Convert between CSV and JSON formats
      </p>
      <FileConverter />
    </div>
  );
}

