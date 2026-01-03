import { readFile } from 'fs/promises';
import path from 'path';

import { NextResponse } from 'next/server';
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

function injectTheme(html: string, theme: 'light' | 'dark') {
  const marker = 'data-formata-pdf-theme="1"';
  if (html.includes(marker)) return html;

  const script = `<script ${marker}>(function(){document.documentElement.dataset.theme=${JSON.stringify(
    theme,
  )}})();</script>`;

  const styleCloseIndex = html.toLowerCase().indexOf('</style>');
  if (styleCloseIndex !== -1) {
    const insertAt = styleCloseIndex + '</style>'.length;
    return `${html.slice(0, insertAt)}${script}${html.slice(insertAt)}`;
  }

  const bodyIndex = html.toLowerCase().indexOf('<body');
  if (bodyIndex !== -1) {
    return `${html.slice(0, bodyIndex)}${script}${html.slice(bodyIndex)}`;
  }

  return `${script}${html}`;
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

export async function GET(request: Request, { params }: { params: { jobId: string } }) {
  const url = new URL(request.url);
  const theme = url.searchParams.get('theme') === 'dark' ? 'dark' : 'light';

  const reportPath = path.join(process.cwd(), `${params.jobId}_clean_profile.html`);
  const fallbackPath = path.join(process.cwd(), 'cf61c556-961f-484d-9110-d25b651ecf67_clean_profile.html');
  const cssPath = path.join(process.cwd(), 'public', 'ydata-profile-theme.css');

  const css = await readFile(cssPath, 'utf8');

  let html: string;
  try {
    html = await readFile(reportPath, 'utf8');
  } catch {
    html = await readFile(fallbackPath, 'utf8');
  }

  html = injectCss(html, css);
  html = injectTheme(html, theme);

  const pdf = await renderPdfFromHtml(html, theme);

  return new NextResponse(pdf, {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': `attachment; filename="formata-error-report-${params.jobId}.pdf"`,
      'Cache-Control': 'no-store',
    },
  });
}

