'use client';

import { FileConverter } from '@/components/FileConverter';
import { Card, CardContent } from '@/components/ui/card';

export default function ConvertPage() {
  return (
    <div className="container mx-auto p-6 max-w-4xl flex flex-col items-center">
      <Card className="w-full max-w-2xl">
        <CardContent className="pt-6 space-y-6 flex flex-col items-center">
          <h1 className="text-3xl font-bold italic uppercase">FILE CONVERSION</h1>
          <p className="text-muted-foreground text-center">
            Convert between CSV and JSON formats
          </p>
          <FileConverter />
        </CardContent>
      </Card>
    </div>
  );
}

