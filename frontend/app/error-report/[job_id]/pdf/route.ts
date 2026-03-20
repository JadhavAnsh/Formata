import { readFile } from 'fs/promises';
import path from 'path';

import { NextResponse } from 'next/server';
import { chromium } from 'playwright';

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

function injectCss(html: string, css: string) {
  const marker = 'data-formata-pdf-css="1"';
  if (html.includes(marker)) return html;

  const injection = `<style ${marker}>${css}</style>`;
  const styleCloseIndex = html.toLowerCase().indexOf('</style>');
  if (styleCloseIndex !== -1) {
    const insertAt = styleCloseIndex + '</style>'.length;
    return `${html.slice(0, insertAt)}${injection}${html.slice(insertAt)}`;
  }

  const bodyIndex = html.toLowerCase().indexOf('<body');
  if (bodyIndex !== -1) {
    return `${html.slice(0, bodyIndex)}${injection}${html.slice(bodyIndex)}`;
  }

  return `${injection}${html}`;
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

async function renderPdfFromHtml(html: string, theme: 'light' | 'dark') {
  const browser = await chromium.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const context = await browser.newContext({
      colorScheme: theme,
      viewport: { width: 1280, height: 720 },
    });
    const page = await context.newPage();

    await page.setContent(html, { waitUntil: 'load' });
    await page.emulateMedia({ media: 'screen' });

    return await page.pdf({
      format: 'A4',
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: '12mm', right: '10mm', bottom: '12mm', left: '10mm' },
    });
  } finally {
    await browser.close();
  }
}

export async function GET(request: Request, { params }: { params: Promise<{ job_id: string }> }) {
  const { job_id } = await params;
  const url = new URL(request.url);
  const theme = url.searchParams.get('theme') === 'dark' ? 'dark' : 'light';
  const jwt = request.headers.get('X-Appwrite-JWT') || url.searchParams.get('jwt');

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';
  const cssPath = path.join(process.cwd(), 'public', 'ydata-profile-theme-v2.css');

  const css = await readFile(cssPath, 'utf8');

  let html: string;

  try {
    // Call backend API to get generated error report
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

    const reportText = await response.text();
    html = wrapErrorTextAsHtml(job_id, reportText);

    if (!html) {
      throw new Error('No error report content in response');
    }
  } catch {
    // Fallback to local text report if API fails
    const reportPath = path.join(process.cwd(), 'storage', 'errors', `${job_id}_errors.txt`);
    const fallbackPath = path.join(process.cwd(), 'storage', 'errors', `${job_id}_error.txt`);

    try {
      const reportText = await readFile(reportPath, 'utf8');
      html = wrapErrorTextAsHtml(job_id, reportText);
    } catch {
      const fallbackText = await readFile(fallbackPath, 'utf8');
      html = wrapErrorTextAsHtml(job_id, fallbackText);
    }
  }

  html = injectCss(html, css);
  html = setRootTheme(html, theme);

  const pdf = await renderPdfFromHtml(html, theme);

  return new NextResponse(Buffer.from(pdf), {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': `attachment; filename="formata-error-report-${job_id}.pdf"`,
      'Cache-Control': 'no-store',
    },
  });
}

