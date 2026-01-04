import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

function getApiBaseUrl(request: Request) {
  const fromEnv = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
  if (fromEnv.startsWith('http://') || fromEnv.startsWith('https://')) return fromEnv;

  const origin = new URL(request.url).origin;
  if (!fromEnv) return origin;
  return `${origin}${fromEnv.startsWith('/') ? '' : '/'}${fromEnv}`;
}

export async function GET(request: NextRequest, context: { params: Promise<{ job_id: string }> }) {
  const { job_id } = await context.params;
  const apiBaseUrl = getApiBaseUrl(request);
  const apiKey = process.env.NEXT_PUBLIC_API_KEY || '';

  const upstream = await fetch(`${apiBaseUrl}/vectors/${job_id}/download?format=pkl`, {
    headers: {
      ...(apiKey && { 'X-API-Key': apiKey }),
    },
    cache: 'no-store',
  });

  if (!upstream.ok || !upstream.body) {
    return new NextResponse('Failed to download file', { status: upstream.status || 500 });
  }

  const contentType = upstream.headers.get('Content-Type') || 'application/octet-stream';
  const contentDisposition =
    upstream.headers.get('Content-Disposition') || `attachment; filename="vectors_${job_id}.pkl"`;

  return new NextResponse(upstream.body, {
    headers: {
      'Content-Type': contentType,
      'Content-Disposition': contentDisposition,
      'Cache-Control': 'no-store',
    },
  });
}
