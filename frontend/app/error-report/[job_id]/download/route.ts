import { readFile } from 'fs/promises';
import path from 'path';

import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

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

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

  try {
    // Call the backend API to get the profile report
    const apiUrl = `${API_BASE_URL}/profile/${job_id}`;
    const response = await fetch(apiUrl, {
      headers: {
        ...(API_KEY && { 'X-API-Key': API_KEY }),
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch profile: ${response.statusText}`);
    }

    const profileData = await response.json();
    const html = profileData.content || profileData.html;

    if (!html) {
      throw new Error('No HTML content in profile response');
    }

    return new NextResponse(injectThemeAssets(html, theme), {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Content-Disposition': `attachment; filename="formata-error-report-${job_id}.html"`,
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    // Fallback to local file if API fails
    const filePath = path.join(process.cwd(), `${job_id}_clean_profile.html`);
    const fallbackPath = path.join(process.cwd(), 'cf61c556-961f-484d-9110-d25b651ecf67_clean_profile.html');

    try {
      const html = await readFile(filePath, 'utf8');
      return new NextResponse(injectThemeAssets(html, theme), {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Content-Disposition': `attachment; filename="formata-error-report-${job_id}.html"`,
          'Cache-Control': 'no-store',
        },
      });
    } catch {
      try {
        const html = await readFile(fallbackPath, 'utf8');
        return new NextResponse(injectThemeAssets(html, theme), {
          headers: {
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Disposition': `attachment; filename="formata-error-report-${job_id}.html"`,
            'Cache-Control': 'no-store',
          },
        });
      } catch {
        return new NextResponse('Report not found', { status: 404 });
      }
    }
  }
}
