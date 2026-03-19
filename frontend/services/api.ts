/**
 * API utility functions for making HTTP requests
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

export interface ApiError {
  message: string;
  status?: number;
  data?: any;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  jwt?: string
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(jwt && { 'X-Appwrite-JWT': jwt }),
    ...((options.headers as Record<string, string>) || {}),
  };

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw {
        message: errorData.message || `HTTP error! status: ${response.status}`,
        status: response.status,
        data: errorData,
      } as ApiError;
    }

    return await response.json();
  } catch (error) {
    if (error && typeof error === 'object' && 'status' in error) {
      throw error;
    }
    throw {
      message: error instanceof Error ? error.message : 'Network error',
    } as ApiError;
  }
}

export async function apiPost<T>(
  endpoint: string,
  data: any,
  jwt?: string
): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  }, jwt);
}

export async function apiGet<T>(
  endpoint: string,
  jwt?: string
): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: 'GET',
  }, jwt);
}

export async function apiUpload(
  endpoint: string,
  file: File,
  additionalData?: Record<string, any>,
  jwt?: string
): Promise<any> {
  const url = `${API_BASE_URL}${endpoint}`;
  const formData = new FormData();
  formData.append('file', file);
  
  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, typeof value === 'string' ? value : JSON.stringify(value));
    });
  }

  const headers: Record<string, string> = {
    ...(jwt && { 'X-Appwrite-JWT': jwt }),
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw {
        message: errorData.message || `HTTP error! status: ${response.status}`,
        status: response.status,
        data: errorData,
      } as ApiError;
    }

    return await response.json();
  } catch (error) {
    if (error && typeof error === 'object' && 'status' in error) {
      throw error;
    }
    throw {
      message: error instanceof Error ? error.message : 'Network error',
    } as ApiError;
  }
}
