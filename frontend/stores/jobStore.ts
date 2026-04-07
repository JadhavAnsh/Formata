import { create } from 'zustand';
import type { Job } from '@/types/job';
import type { ProcessingResult } from '@/services/result.service';

interface JobStoreState {
  currentJobId: string | null;
  jobs: Record<string, Job>;
  results: Record<string, ProcessingResult>;
  setCurrentJobId: (jobId: string | null) => void;
  upsertJob: (job: Job) => void;
  setResult: (jobId: string, result: ProcessingResult) => void;
  clearJob: (jobId: string) => void;
}

export const useJobStore = create<JobStoreState>((set) => ({
  currentJobId: null,
  jobs: {},
  results: {},
  setCurrentJobId: (jobId) => set({ currentJobId: jobId }),
  upsertJob: (job) =>
    set((state) => ({
      jobs: {
        ...state.jobs,
        [job.job_id || job.id]: job,
      },
    })),
  setResult: (jobId, result) =>
    set((state) => ({
      results: {
        ...state.results,
        [jobId]: result,
      },
    })),
  clearJob: (jobId) =>
    set((state) => {
      const nextJobs = { ...state.jobs };
      const nextResults = { ...state.results };
      delete nextJobs[jobId];
      delete nextResults[jobId];
      return { jobs: nextJobs, results: nextResults };
    }),
}));
