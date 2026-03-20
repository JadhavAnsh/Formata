import { readFile } from 'fs/promises';
import path from 'path';

import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function GET(request: Request, { params }: { params: Promise<{ job_id: string }> }) {
  const { job_id } = await params;
  const url = new URL(request.url);
  const jwt = request.headers.get('X-Appwrite-JWT') || url.searchParams.get('jwt');

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

  try {
    // Call the backend API to get generated error report file
    const apiUrl = `${API_BASE_URL}/errors/${job_id}/download`;
    const response = await fetch(apiUrl, {
      headers: {
        ...(jwt && { 'X-Appwrite-JWT': jwt }),
        ...(API_KEY && { 'X-API-Key': API_KEY }),
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const detail = errorData?.detail || response.statusText;
      throw new Error(`Failed to fetch error report: ${detail}`);
    }

    const reportContent = await response.text();

    return new NextResponse(reportContent, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Disposition': `attachment; filename="${job_id}_errors.txt"`,
        'Cache-Control': 'no-store',
      },
    });
  } catch {
    // Fallback to local text report if API fails
    const filePath = path.join(process.cwd(), 'storage', 'errors', `${job_id}_errors.txt`);
    const fallbackPath = path.join(process.cwd(), 'storage', 'errors', `${job_id}_error.txt`);

    try {
      const reportContent = await readFile(filePath, 'utf8');
      return new NextResponse(reportContent, {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Content-Disposition': `attachment; filename="${job_id}_errors.txt"`,
          'Cache-Control': 'no-store',
        },
      });
    } catch {
      try {
        const reportContent = await readFile(fallbackPath, 'utf8');
        return new NextResponse(reportContent, {
          headers: {
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Disposition': `attachment; filename="${job_id}_errors.txt"`,
            'Cache-Control': 'no-store',
          },
        });
      } catch {
        return new NextResponse('Report not found', { status: 404 });
      }
    }
  }
}
