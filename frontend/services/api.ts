/**
 * API utility functions for making HTTP requests
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

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
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(API_KEY && { 'X-API-Key': API_KEY }),
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiRequestError(getErrorMessage(errorData, response.status), response.status, errorData);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiRequestError) {
      throw error;
    }

    throw new ApiRequestError(error instanceof Error ? error.message : 'Network error');
  }
}

export async function apiUpload(
  endpoint: string,
  file: File,
  additionalData?: Record<string, any>
): Promise<any> {
  const url = `${API_BASE_URL}${endpoint}`;
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

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiRequestError(getErrorMessage(errorData, response.status), response.status, errorData);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiRequestError) {
      throw error;
    }

    throw new ApiRequestError(error instanceof Error ? error.message : 'Network error');
  }
}

