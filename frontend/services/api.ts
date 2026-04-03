/**
 * API utility functions for making HTTP requests
 */

const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

function isLocalHostname(hostname: string): boolean {
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1';
}

function resolveApiBaseUrl(): string {
  const configured = (DEFAULT_API_BASE_URL || '').trim();
  if (!configured) {
    return 'http://localhost:8000';
  }

  if (typeof window === 'undefined') {
    return configured;
  }

  try {
    const parsed = new URL(configured);
    const browserHost = window.location.hostname;

    // If frontend is accessed via LAN/IP but API URL is localhost,
    // rewrite hostname so browser reaches the correct backend host.
    if (isLocalHostname(parsed.hostname) && !isLocalHostname(browserHost)) {
      parsed.hostname = browserHost;
      return parsed.toString().replace(/\/$/, '');
    }

    return configured;
  } catch {
    return configured;
  }
}

function normalizeBase(base: string): string {
  return base.replace(/\/$/, '');
}

function getApiBaseCandidates(): string[] {
  const primary = normalizeBase(resolveApiBaseUrl());
  const candidates = [primary];

  if (typeof window === 'undefined') {
    return candidates;
  }

  try {
    const parsed = new URL(primary);
    if (!isLocalHostname(parsed.hostname)) {
      return candidates;
    }

    const hostCandidates = [window.location.hostname, 'localhost', '127.0.0.1']
      .map((h) => h.trim())
      .filter(Boolean);

    for (const host of hostCandidates) {
      const next = new URL(parsed.toString());
      next.hostname = host;
      const nextBase = normalizeBase(next.toString());
      if (!candidates.includes(nextBase)) {
        candidates.push(nextBase);
      }
    }
  } catch {
    // Keep primary candidate only.
  }

  return candidates;
}

async function fetchWithTimeout(url: string, config: RequestInit, timeoutMs = 30000): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...config, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export interface ApiError {
  message: string;
  status?: number;
  data?: any;
}

export class ApiRequestError extends Error {
  status?: number;
  data?: any;

  constructor(message: string, status?: number, data?: any) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.data = data;
  }
}

function getErrorMessage(errorData: any, status: number): string {
  if (typeof errorData?.message === 'string' && errorData.message.trim()) {
    return errorData.message;
  }

  if (typeof errorData?.detail === 'string' && errorData.detail.trim()) {
    return errorData.detail;
  }

  return `HTTP error! status: ${status}`;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(API_KEY && { 'X-API-Key': API_KEY }),
      ...options.headers,
    },
  };

  const baseCandidates = getApiBaseCandidates();
  let lastNetworkError: unknown = null;

  for (const base of baseCandidates) {
    const url = `${base}${endpoint}`;
    try {
      const response = await fetchWithTimeout(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiRequestError(getErrorMessage(errorData, response.status), response.status, errorData);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiRequestError) {
        throw error;
      }
      lastNetworkError = error;
    }
  }

  const message = lastNetworkError instanceof Error ? lastNetworkError.message : 'Network error';
  throw new ApiRequestError(
    `Failed to reach API endpoint ${endpoint}. Tried: ${baseCandidates.join(', ')}. ${message}`
  );
}

export async function apiRequestRaw(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const config: RequestInit = {
    ...options,
    headers: {
      ...(API_KEY && { 'X-API-Key': API_KEY }),
      ...options.headers,
    },
  };

  const baseCandidates = getApiBaseCandidates();
  let lastNetworkError: unknown = null;

  for (const base of baseCandidates) {
    const url = `${base}${endpoint}`;
    try {
      const response = await fetchWithTimeout(url, config, 60000);

      if (!response.ok) {
        const errorData = await response.clone().json().catch(() => ({}));
        throw new ApiRequestError(getErrorMessage(errorData, response.status), response.status, errorData);
      }

      return response;
    } catch (error) {
      if (error instanceof ApiRequestError) {
        throw error;
      }
      lastNetworkError = error;
    }
  }

  const message = lastNetworkError instanceof Error ? lastNetworkError.message : 'Network error';
  throw new ApiRequestError(
    `Failed to reach API endpoint ${endpoint}. Tried: ${baseCandidates.join(', ')}. ${message}`
  );
}

export async function apiUpload(
  endpoint: string,
  file: File,
  additionalData?: Record<string, any>
): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  
  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, typeof value === 'string' ? value : JSON.stringify(value));
    });
  }

  const headers: HeadersInit = {};
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }

  const config: RequestInit = {
      method: 'POST',
      headers,
      body: formData,
  };

  const baseCandidates = getApiBaseCandidates();
  let lastNetworkError: unknown = null;

  for (const base of baseCandidates) {
    const url = `${base}${endpoint}`;
    try {
      const response = await fetchWithTimeout(url, config, 60000);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiRequestError(getErrorMessage(errorData, response.status), response.status, errorData);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiRequestError) {
        throw error;
      }
      lastNetworkError = error;
    }
  }

  const message = lastNetworkError instanceof Error ? lastNetworkError.message : 'Network error';
  throw new ApiRequestError(
    `Failed to reach API endpoint ${endpoint}. Tried: ${baseCandidates.join(', ')}. ${message}`
  );
}

