import { readFile } from 'fs/promises';
import path from 'path';

import { NextRequest, NextResponse } from 'next/server';
import { chromium } from 'playwright';

export const runtime = 'nodejs';

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

export async function GET(request: NextRequest, context: { params: Promise<{ job_id: string }> }) {
  const { job_id } = await context.params;
  const url = new URL(request.url);
  const theme = url.searchParams.get('theme') === 'dark' ? 'dark' : 'light';

  const reportPath = path.join(process.cwd(), `${job_id}_clean_profile.html`);
  const fallbackPath = path.join(process.cwd(), 'cf61c556-961f-484d-9110-d25b651ecf67_clean_profile.html');
  const cssPath = path.join(process.cwd(), 'public', 'ydata-profile-theme-v2.css');

  const css = await readFile(cssPath, 'utf8');

  let html: string;
  try {
    html = await readFile(reportPath, 'utf8');
  } catch {
    html = await readFile(fallbackPath, 'utf8');
  }

  html = injectCss(html, css);
  html = setRootTheme(html, theme);

  const pdf = await renderPdfFromHtml(html, theme);
  const pdfBytes = new Uint8Array(pdf);

  return new NextResponse(pdfBytes, {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': `attachment; filename="formata-error-report-${job_id}.pdf"`,
      'Cache-Control': 'no-store',
    },
  });
}

