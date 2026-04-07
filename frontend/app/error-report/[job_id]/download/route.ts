import { readFile } from 'fs/promises';
import path from 'path';

import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

async function extractProfileHtml(response: Response): Promise<string> {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const payload = await response.json();
    const html = payload?.content || payload?.html;
    if (!html) {
      throw new Error('No HTML content in profile response');
    }
    return html;
  }
  return response.text();
}

export async function GET(request: Request, { params }: { params: Promise<{ job_id: string }> }) {
  const { job_id } = await params;
  const url = new URL(request.url);
  const jwt = request.headers.get('X-Appwrite-JWT') || url.searchParams.get('jwt');

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

  try {
    // Call backend profile API (ydata-profiling report)
    const apiUrl = `${API_BASE_URL}/profile/${job_id}`;
    const response = await fetch(apiUrl, {
      headers: {
        ...(jwt && { 'X-Appwrite-JWT': jwt }),
        ...(API_KEY && { 'X-API-Key': API_KEY }),
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const detail = errorData?.detail || response.statusText;
      throw new Error(`Failed to fetch profile report: ${detail}`);
    }

    const reportContent = await extractProfileHtml(response);

    return new NextResponse(reportContent, {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Content-Disposition': `attachment; filename="formata-profile-${job_id}.html"`,
        'Cache-Control': 'no-store',
      },
    });
  } catch {
    // Fallback to local profile HTML if API fails
    const filePath = path.join(process.cwd(), 'storage', 'reports', `${job_id}_clean_profile.html`);
    const fallbackPath = path.join(process.cwd(), `${job_id}_clean_profile.html`);

    try {
      const reportContent = await readFile(filePath, 'utf8');
      return new NextResponse(reportContent, {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Content-Disposition': `attachment; filename="formata-profile-${job_id}.html"`,
          'Cache-Control': 'no-store',
        },
      });
    } catch {
      try {
        const reportContent = await readFile(fallbackPath, 'utf8');
        return new NextResponse(reportContent, {
          headers: {
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Disposition': `attachment; filename="formata-profile-${job_id}.html"`,
            'Cache-Control': 'no-store',
          },
        });
      } catch {
        return new NextResponse('Report not found', { status: 404 });
      }
    }
  }
}
