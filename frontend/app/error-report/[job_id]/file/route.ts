import { readFile } from 'fs/promises';
import path from 'path';

import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function wrapErrorTextAsHtml(jobId: string, errorText: string) {
  const body = escapeHtml(errorText || 'No errors to report.');
  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Formata Error Report - ${escapeHtml(jobId)}</title>
  </head>
  <body>
    <main style="max-width: 1200px; margin: 24px auto; padding: 0 16px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;">
      <h1 style="font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;">Error Report</h1>
      <p style="font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; opacity: 0.8;">Job ID: ${escapeHtml(jobId)}</p>
      <pre style="white-space: pre-wrap; word-break: break-word; border: 1px solid #d4d4d8; border-radius: 8px; padding: 16px;">${body}</pre>
    </main>
  </body>
</html>`;
}

function setRootTheme(html: string, theme: 'light' | 'dark') {
  const htmlTagMatch = html.match(/<html\b[^>]*>/i);
  if (!htmlTagMatch) return html;

  const originalTag = htmlTagMatch[0];
  let nextTag = originalTag;

  if (/data-theme\s*=\s*["'][^"']*["']/i.test(nextTag)) {
    nextTag = nextTag.replace(/data-theme\s*=\s*["'][^"']*["']/i, `data-theme="${theme}"`);
  } else {
    nextTag = nextTag.replace(/<html\b/i, `<html data-theme="${theme}"`);
  }

  const styleAttrMatch = nextTag.match(/style\s*=\s*["']([^"']*)["']/i);
  const colorSchemeDecl = `color-scheme: ${theme};`;
  if (styleAttrMatch) {
    const existingStyle = styleAttrMatch[1] ?? '';
    const cleanedStyle = existingStyle.replace(/color-scheme\s*:\s*(light|dark)\s*;?/gi, '').trim();
    const mergedStyle = `${cleanedStyle}${cleanedStyle ? '; ' : ''}${colorSchemeDecl}`.trim();
    nextTag = nextTag.replace(styleAttrMatch[0], `style="${mergedStyle}"`);
  } else {
    nextTag = nextTag.replace(/>$/, ` style="${colorSchemeDecl}">`);
  }

  return html.replace(originalTag, nextTag);
}

function injectThemeAssets(html: string, theme?: 'light' | 'dark') {
  const marker = 'data-formata-theme-assets="1"';
  if (html.includes(marker)) return html;

  const headInjection = [
    `<meta ${marker} name="color-scheme" content="light dark">`,
    `<link ${marker} rel="stylesheet" href="/ydata-profile-theme-v2.css">`,
  ].join('');

  const themeInjection =
    theme === 'dark' || theme === 'light'
      ? ''
      : `<script ${marker}>(function(){try{var e=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)');document.documentElement.dataset.theme=e&&e.matches?'dark':'light';if(e&&e.addEventListener)e.addEventListener('change',function(){document.documentElement.dataset.theme=e.matches?'dark':'light'})}catch(t){}})();</script>`;

  const themedHtml = theme ? setRootTheme(html, theme) : html;

  const headOpenMatch = themedHtml.match(/<head\b[^>]*>/i);
  if (headOpenMatch) {
    const insertAt = (headOpenMatch.index ?? 0) + headOpenMatch[0].length;
    return `${themedHtml.slice(0, insertAt)}${headInjection}${themeInjection}${themedHtml.slice(insertAt)}`;
  }

  const bodyIndex = themedHtml.toLowerCase().indexOf('<body');
  if (bodyIndex !== -1) {
    return `${themedHtml.slice(0, bodyIndex)}${headInjection}${themeInjection}${themedHtml.slice(bodyIndex)}`;
  }

  return `${headInjection}${themeInjection}${themedHtml}`;
}

export async function GET(request: Request, { params }: { params: Promise<{ job_id: string }> }) {
  const { job_id } = await params;
  const url = new URL(request.url);
  const theme = url.searchParams.get('theme') === 'dark' ? 'dark' : url.searchParams.get('theme') === 'light' ? 'light' : undefined;

  const jwt = request.headers.get('X-Appwrite-JWT') || url.searchParams.get('jwt');

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

  try {
    // Call the backend API to get the generated error report
    const apiUrl = `${API_BASE_URL}/errors/${job_id}/download`;
    console.log(`Fetching error report from: ${apiUrl} (JWT provided: ${!!jwt})`);
    const response = await fetch(apiUrl, {
      headers: {
        ...(jwt && { 'X-Appwrite-JWT': jwt }),
        ...(API_KEY && { 'X-API-Key': API_KEY }),
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const detail = errorData?.detail || response.statusText;
      console.error(`Backend returned ${response.status}: ${detail}`);
      throw new Error(`Failed to fetch error report: ${detail}`);
    }

    const errorText = await response.text();
    const html = wrapErrorTextAsHtml(job_id, errorText);

    if (!html) {
      throw new Error('No content in error report response');
    }

    return new NextResponse(injectThemeAssets(html, theme), {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store',
      },
    });
  } catch {
    // Fallback to local text report if API fails
    const filePath = path.join(process.cwd(), 'storage', 'errors', `${job_id}_errors.txt`);
    const fallbackPath = path.join(process.cwd(), 'storage', 'errors', `${job_id}_error.txt`);

    try {
      const errorText = await readFile(filePath, 'utf8');
      const html = wrapErrorTextAsHtml(job_id, errorText);
      return new NextResponse(injectThemeAssets(html, theme), {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'no-store',
        },
      });
    } catch {
      try {
        const errorText = await readFile(fallbackPath, 'utf8');
        const html = wrapErrorTextAsHtml(job_id, errorText);
        return new NextResponse(injectThemeAssets(html, theme), {
          headers: {
            'Content-Type': 'text/html; charset=utf-8',
            'Cache-Control': 'no-store',
          },
        });
      } catch {
        return new NextResponse('Report not found', { status: 404 });
      }
    }
  }
}
