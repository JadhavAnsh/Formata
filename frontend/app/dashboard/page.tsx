'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { jobsService } from '@/services/jobs.service';
import type { Job } from '@/types/job';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Trash2, RefreshCw, ExternalLink } from 'lucide-react';

export default function DashboardPage() {
  const { getJwt, user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const jwt = await getJwt();
      if (!jwt) throw new Error('Not authenticated');
      const data = await jobsService.listJobs(jwt);
      setJobs(data.sort((a, b) => 
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      ));
    } catch (err: any) {
      setError(err.message || 'Failed to load jobs');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleDelete = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job?')) return;
    
    try {
      const jwt = await getJwt();
      await jobsService.deleteJob(jobId, jwt || undefined);
      setJobs(jobs.filter(j => j.id !== jobId));
    } catch (err: any) {
      alert('Failed to delete job: ' + err.message);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-500">Completed</Badge>;
      case 'processing':
        return <Badge className="bg-blue-500 animate-pulse">Processing</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'pending':
        return <Badge variant="outline">Pending</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 mt-16">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Your Jobs</h1>
          <p className="text-muted-foreground">Manage and track your data processing tasks</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={fetchJobs} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
          <Link href="/ingest">
            <Button>New Job</Button>
          </Link>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-md mb-6">
          {error}
        </div>
      )}

      <div className="grid gap-4">
        {isLoading && jobs.length === 0 ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : jobs.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center py-12">
              <p className="text-muted-foreground mb-4">No jobs found</p>
              <Link href="/ingest">
                <Button variant="outline">Start your first job</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          jobs.map((job) => (
            <Card key={job.id} className="overflow-hidden">
              <CardContent className="p-0">
                <div className="flex flex-col sm:flex-row items-center p-4 gap-4">
                  <div className="flex-1 w-full">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold truncate max-w-[200px] sm:max-w-[400px]">
                        {job.filename}
                      </h3>
                      {getStatusBadge(job.status)}
                    </div>
                    <div className="text-xs text-muted-foreground flex gap-3">
                      <span>ID: {job.id.substring(0, 8)}...</span>
                      <span>Created: {new Date(job.createdAt).toLocaleString()}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                    {job.status === 'completed' ? (
                      <Link href={`/result/${job.id}`}>
                        <Button size="sm" variant="outline" className="gap-1">
                          View Result <ExternalLink className="h-3 w-3" />
                        </Button>
                      </Link>
                    ) : job.status === 'processing' || job.status === 'pending' ? (
                      <Link href={`/process/${job.id}`}>
                        <Button size="sm" variant="outline" className="gap-1">
                          Track Progress <Loader2 className="h-3 w-3 animate-spin" />
                        </Button>
                      </Link>
                    ) : null}
                    
                    <Button 
                      size="sm" 
                      variant="ghost" 
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      onClick={() => handleDelete(job.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                {job.status === 'processing' && (
                  <div className="h-1 bg-muted w-full">
                    <div 
                      className="h-full bg-blue-500 transition-all duration-500" 
                      style={{ width: `${job.progress || 0}%` }}
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
