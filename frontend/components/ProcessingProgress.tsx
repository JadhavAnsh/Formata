'use client';

import { Loader2 } from 'lucide-react';
import { ProgressBar } from '@/components/ProgressBar';
import { Card, CardContent } from '@/components/ui/card';

interface ProcessingProgressProps {
  jobId: string;
  progress: number;
  stage: string;
}

export function ProcessingProgress({ jobId, progress, stage }: ProcessingProgressProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="size-9 rounded-full bg-primary/15 ring-1 ring-primary/25 flex items-center justify-center">
            <Loader2 className="size-4 animate-spin text-primary" />
          </div>
          <div>
            <div className="text-base font-semibold leading-tight">Processing</div>
            <div className="text-sm text-muted-foreground">{stage}</div>
          </div>
        </div>

        <div className="text-muted-foreground text-sm mb-6">
          <span className="opacity-80">Job ID:</span> <span className="break-all">{jobId}</span>
        </div>

        <ProgressBar progress={progress} status={stage} />

        <div className="mt-5 grid grid-cols-3 gap-2">
          <div className="h-1.5 rounded-full bg-primary/20 overflow-hidden">
            <div className="h-full w-full bg-primary/60 animate-[pulse_1.2s_ease-in-out_infinite]" />
          </div>
          <div className="h-1.5 rounded-full bg-primary/15 overflow-hidden">
            <div className="h-full w-full bg-primary/50 animate-[pulse_1.4s_ease-in-out_infinite]" />
          </div>
          <div className="h-1.5 rounded-full bg-primary/10 overflow-hidden">
            <div className="h-full w-full bg-primary/40 animate-[pulse_1.6s_ease-in-out_infinite]" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

