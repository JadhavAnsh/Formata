/**
 * Centralized TanStack Query keys — use for prefetch, invalidation, and hydration.
 */
export const queryKeys = {
  jobStatus: (jobId: string) => ['job-status', jobId] as const,
  jobResult: (jobId: string) => ['job-result', jobId] as const,
};
