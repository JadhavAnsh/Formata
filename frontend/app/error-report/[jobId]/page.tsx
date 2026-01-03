import Link from 'next/link';

import { Button } from '@/components/ui/button';

interface ErrorReportPageProps {
  params: Promise<{
    jobId: string;
  }>;
}

export default async function ErrorReportPage({ params }: ErrorReportPageProps) {
  const { jobId } = await params;

  return (
    <div className="min-h-screen pt-24 sm:pt-28 pb-16 px-4 sm:px-6 relative">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_0%,rgba(124,58,237,0.12)_0%,transparent_55%)]" />
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold leading-tight">Error Report</h1>
            <p className="text-sm text-muted-foreground break-all">
              <span className="opacity-80">Job ID:</span> {jobId}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
            <Button variant="outline" className="w-full sm:w-auto" asChild>
              <Link href={`/result/${jobId}`}>Back to Results</Link>
            </Button>
            <Button className="w-full sm:w-auto" asChild>
              <a href={`/error-report/${jobId}/pdf`}>Download PDF</a>
            </Button>
          </div>
        </div>

        <div className="border rounded-lg overflow-hidden bg-background">
          <iframe title="Error report" src={`/error-report/${jobId}/file`} className="w-full h-[75vh]" />
        </div>
      </div>
    </div>
  );
}
